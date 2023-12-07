from zenml import step
import tensorflow as tf
import ray
from ray import serve
from fastapi import FastAPI, File, UploadFile
import numpy as np
import io
from PIL import Image


@step()
def deploy(model: tf.keras.Sequential) -> None:
    app = FastAPI()

    @serve.deployment(name="Fashion", num_replicas=1, ray_actor_options={"num_cpus": 0.2})
    @serve.ingress(app)
    class Fashion:
        def __init__(self):
            self.model: tf.keras.Sequential = model

        @app.post("/")
        async def classify_image(self, file: UploadFile = File(...)):
            image_bytes = await file.read()

            # Load the image with PIL
            image = Image.open(io.BytesIO(image_bytes))

            image = image.convert('L').resize((28, 28))

            # Convert the image to a numpy array and scale it to the [0, 1] range
            image = np.array(image).astype("float32") / 255

            # Reshape from (28, 28) to (784)
            image = np.reshape(image, (784,))

            # Expand dimensions to represent a batch of size 1
            image = np.expand_dims(image, axis=0)

            # Make a prediction
            result = self.model.predict(image)
            prediction = np.argmax(result, axis=1)

            # Return the prediction
            return {"class_index": prediction}

    ray.init(address="ray://193.2.205.27:10001", ignore_reinit_error=True)
    serve.run(Fashion.bind(), name="Fashion", route_prefix="/fashion")
    serve.delete("text_ml_app")  # placeholder removal
