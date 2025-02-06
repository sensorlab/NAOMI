import os
import numpy as np

from fastapi import FastAPI, HTTPException
import tensorflow as tf
from tensorflow import keras

import ray
from ray import serve

from flytekit import task
from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec
from flytekit import PodTemplate


def get_pod_template():
    return PodTemplate(
        pod_spec=V1PodSpec(
            node_selector={
                "kubernetes.io/arch": "amd64"
            },
            containers=[
                V1Container(
                    name="primary",
                    resources=V1ResourceRequirements(
                        limits={"memory": "2Gi", "cpu": "1000m"},
                        requests={"memory": "1Gi"}
                    ),
                ),
            ],
        )
    )

SYSTEM_IP = os.environ.get('SYSTEM_IP')


@task(pod_template=get_pod_template())
def deploy(model: keras.Model, num_replicas: int = 1) -> None:
    """
    Deploy the trained MobileNetV1 model for VWW using Ray Serve.
    Expose a FastAPI endpoint to handle predictions.
    """

    app = FastAPI(debug=True)

    @serve.deployment(
        name="vww_classification",
        num_replicas=num_replicas,
        ray_actor_options={"num_cpus": 0, "num_gpus": 0, "memory": 0},
    )
    @serve.ingress(app)
    class VWWInferenceService:
        def __init__(self):
            # Load the model passed from the train step
            self.model = model

        @app.post("/")
        async def classify(self, data: dict):
            """
            Send JSON with key "instances",
            e.g. {"instances": [[[pixels], ...]]}
            for shape (1, 96, 96, 3) or more samples.
            """
            try:
                instances = data.get("instances", [])
                instances = np.array(instances, dtype=np.float32)
                # Model expects input scaled to approx [-1..1],
                # so do that if needed or ensure the client does it.

                preds = self.model.predict(instances)
                # preds has shape (N, 2) => softmax => [prob_person, prob_non_person]

                return {"predictions": preds.tolist()}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/health")
        async def health(self):
            return {"status": "ok"}

    runtime_env = {"pip": ["silabs-mltk[full]==0.19.0"]}
    # Initialize Ray (point to your Ray cluster)
    ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True, runtime_env=runtime_env)

    serve.start(detached=True)
    serve.run(VWWInferenceService.bind(), name="Visual_Wake_Words", route_prefix="/VWW")
    serve.delete("Test")  # placeholder removal


    print("Deployment completed, service is live at:")