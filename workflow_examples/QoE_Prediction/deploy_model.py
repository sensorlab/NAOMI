import numpy as np
from flytekit import task
import keras
from fastapi import FastAPI, HTTPException
import os
from .create_features import get_pod_template

# Get system ip from container environment variable set with pyflyte --env SYSTEM_IP=xxx
SYSTEM_IP = os.environ.get('SYSTEM_IP')

@task(pod_template=get_pod_template())
def deploy(model: keras.Sequential, max_replicas: int, ray_workers: int = 1) -> None:
    import ray
    from ray import serve
    app = FastAPI(debug=True, timeout=1000)

    @serve.deployment(
    name="qoe_prediction",
    max_ongoing_requests=2000,
    ray_actor_options={"num_cpus": 1, "num_gpus": 0},
    autoscaling_config={
        "min_replicas": 1, 
        "max_replicas": max_replicas,
        "target_num_ongoing_requests_per_replica": 10,
        "upscale_delay_s": 10,  # Default is 30 seconds
        "downscale_delay_s": 30,  # Default is 600 seconds (10 minutes)
    }
    )
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
