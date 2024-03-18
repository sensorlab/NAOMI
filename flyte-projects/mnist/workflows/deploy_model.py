from flytekit import task, PodTemplate
import keras
import ray
from kubernetes.client import V1PodSpec, V1ResourceRequirements, V1Container
from ray import serve
from fastapi import FastAPI, File, UploadFile, HTTPException
import numpy as np
import io
from PIL import Image
from typing import Annotated




@task(pod_template=PodTemplate(
    pod_spec=V1PodSpec(
        node_selector={
            "kubernetes.io/arch": "amd64"
        },
        containers=[
            V1Container(
                name="primary",
                resources=V1ResourceRequirements(
                    limits={
                        "memory": "2Gi",
                        "cpu": "1000m"
                    },
                    requests={
                        "memory": "1Gi"
                    }
                ),
            ),
        ],
    )
)
)
def deploy(model: keras.Sequential, num_replicas: int) -> None:
    app = FastAPI(debug=True)

    @serve.deployment(name="mnist", num_replicas=num_replicas, ray_actor_options={"num_cpus": 1, "num_gpus": 0}, max_concurrent_queries=100000) # , "resources": {"rasp":0.25}
    @serve.ingress(app)
    class Hello:
        def __init__(self):
            self.model: keras.Sequential = model

        @app.post("/")
        async def classify_image(self, file: Annotated[bytes, File()]):
            try:
                # Load the image with PIL
                image = Image.open(io.BytesIO(file))

                # Convert the image to grayscale and resize it to 28x28
                image = image.convert('L').resize((28, 28))

                # Convert the image to a numpy array and scale it to the [0, 1] range
                image_array = np.array(image).astype("float32") / 255

                # Make sure the image has shape (28, 28, 1)
                image_array = np.expand_dims(image_array, -1)

                # Add an extra dimension for the batch size
                image_array = np.expand_dims(image_array, 0)

                # Make a prediction
                result = self.model.predict(image_array)
                prediction = int(np.argmax(result, axis=1))

                # Return the prediction
                return {"class_index": prediction}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

        @app.post("/test")
        def get(self):
            return "Welcome to the PyTorch model server."

    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)
    serve.run(Hello.bind(), name="mnist", route_prefix="/mnist")
    serve.delete("Test")  # placeholder removal
