import numpy as np
from flytekit import task, PodTemplate
import keras
import ray
from kubernetes.client import V1PodSpec, V1ResourceRequirements, V1Container
from ray import serve
from fastapi import FastAPI, HTTPException

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

    @serve.deployment(name="qoe_prediction", num_replicas=num_replicas, ray_actor_options={"num_cpus": 1, "num_gpus": 0}, max_concurrent_queries=100000) # , "resources": {"rasp":0.25}
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

    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)
    serve.run(Qoe.bind(), name="qoe_prediction", route_prefix="/qoe")
    serve.delete("Test")  # placeholder removal
