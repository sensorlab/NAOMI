import numpy as np
from flytekit import task
import keras
import ray
from ray import serve
from fastapi import FastAPI, HTTPException
import os

from .create_features import get_pod_template

# Get system ip from container environment variable set with pyflyte --env SYSTEM_IP=xxx
SYSTEM_IP = os.environ.get('SYSTEM_IP')

@task(pod_template=get_pod_template())
def deploy(model: keras.Sequential, num_replicas: int) -> None:
    app = FastAPI(debug=True)

    @serve.deployment(name="qoe_prediction", num_replicas="auto",
                      ray_actor_options={"num_cpus": 0, "num_gpus": 0, "memory": 0},
                      autoscaling_config={"min_replicas": 1, "max_replicas": 1})  # , "resources": {"rasp":0.25}
    @serve.ingress(app)
    class Qoe:
        def __init__(self):
            self.model: keras.Sequential = model

        @app.post("/")
        async def qoe_prediction(self, data: dict):
            try:
                # Extract instances from the input data
                instances = data.get("instances", [])

                # convert
                instances = np.array(instances, dtype=np.float32)

                # Perform prediction using your model
                result = model.predict(instances)
                print(result)

                # Return the prediction
                return {"class_index": str(result)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

        @app.post("/test")
        def get(self):
            return "Welcome to the model server."

    ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True)
    serve.run(Qoe.bind(), name="qoe_prediction", route_prefix="/qoe")
    serve.delete("Test")  # placeholder removal
