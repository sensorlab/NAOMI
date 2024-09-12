from flytekit import task
import keras
import ray
from ray import serve
from fastapi import FastAPI, File, UploadFile, HTTPException
import numpy as np
import io
from PIL import Image
from typing import Annotated
import os

from .fetch import get_pod_template

# Get system ip from container environment variable set with pyflyte --env SYSTEM_IP=xxx
SYSTEM_IP = os.environ.get('SYSTEM_IP')

@task(pod_template=get_pod_template())
def deploy(model: keras.Sequential, num_replicas: int) -> None:
    app = FastAPI(debug=True)

    @serve.deployment(name="mnist", num_replicas=num_replicas, ray_actor_options={"num_cpus": 0, "num_gpus": 0}) # , "resources": {"rasp":0.25}
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

    ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True)
    serve.run(Hello.bind(), name="mnist", route_prefix="/mnist")
    serve.delete("Test")  # placeholder removal
