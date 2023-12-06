import keras
from zenml import step


@step()
def deploy(model: keras.Sequential) -> None:
    import keras
    import ray
    from ray import serve
    from fastapi import FastAPI, File, UploadFile
    import numpy as np
    import io
    from PIL import Image
    from typing import List
    from zenml.client import Client
    
    app = FastAPI(debug=True)

    @serve.deployment(name="mnist", num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
    @serve.ingress(app)
    class Hello:
        def __init__(self):
            self.model: keras.Sequential = model
            
        @app.post("/")
        async def classify_image(self, file: UploadFile = File(...)):
            # Read the image file
            image_bytes = await file.read()

            # Load the image with PIL
            image = Image.open(io.BytesIO(image_bytes))

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
            prediction = np.argmax(result, axis=1)

            # Return the prediction
            return {"class_index": prediction}
        
        @app.post("/test")
        def get(self):
            return "Welcome to the PyTorch model server."
        

    ray.init(address="ray://193.2.205.27:10001", ignore_reinit_error=True)
    serve.run(Hello.bind(), name="mnist", route_prefix="/mnist")
    serve.delete("text_ml_app") # placeholder removal


# curl -X POST "http://193.2.205.27/ray-api/" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@my.png"
