import tensorflow as tf
from zenml import step


@step()
def deploy(model: tf.keras.Sequential) -> None:
    import tensorflow as tf
    import ray
    from ray import serve
    from fastapi import FastAPI, File, UploadFile
    import numpy as np
    import io
    from PIL import Image
    from typing import List

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
            image = np.array(image)

            # Reshape from (28, 28) to (28*28=784)
            image = np.reshape(image, 784)

            image = image.astype(np.float32)

            # Convert the pixel values from integers between 0 and 255 to floats between 0 and 1
            image /= 255

            # Make a prediction
            result = self.model.predict(image)
            prediction = np.argmax(result, axis=1)

            # Return the prediction
            return {"class_index": prediction}

    ray.init(address="ray://193.2.205.27:10001", ignore_reinit_error=True)
    serve.run(Fashion.bind(), name="Fashion", route_prefix="/fashion")
    serve.delete("text_ml_app")  # placeholder removal
