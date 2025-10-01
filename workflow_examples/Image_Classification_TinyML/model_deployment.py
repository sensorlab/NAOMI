import os
import numpy as np

from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec
from flytekit import task, PodTemplate
from fastapi import FastAPI, HTTPException
from flytekit import task

import tensorflow as tf
from tensorflow import keras

# from .data_extraction import get_pod_template
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

SYSTEM_IP = os.environ.get('SYSTEM_IP')


@task(pod_template=get_pod_template())
def deploy(model: any, num_replicas: int = 1) -> None:
    """
    Deploy the trained Keras model as a Ray Serve deployment,
    exposing a FastAPI endpoint for inference.
    """

    import ray
    from ray import serve

    # Create a FastAPI application for your deployment
    app = FastAPI(debug=True)

    # Ray Serve Deployment definition
    @serve.deployment(
        name="image_classification",
        num_replicas=num_replicas,
        ray_actor_options={"num_cpus": 0, "num_gpus": 0, "memory": 0},
        # autoscaling_config={"min_replicas": 1, "max_replicas": 2}
    )
    @serve.ingress(app)
    class ImageClassifier:
        """Ray Serve deployment class wrapping a trained Keras model."""

        def __init__(self):
            # Receive the model passed into the deploy() task
            self.model = model

        @app.post("/")
        async def predict_instances(self, data: dict):
            """
            POST JSON with key "instances",
            e.g. {"instances": [[pixel_vals], [pixel_vals], ...]}
            for multiple images.
            """
            try:
                instances = data.get("instances", [])
                instances = np.array(instances, dtype=np.float32)

                # Perform prediction using the loaded model
                predictions = self.model.predict(instances)

                # Return the raw predictions or do further processing
                return {"predictions": predictions.tolist()}
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing request: {str(e)}"
                )

        @app.get("/health")
        async def health_check(self):
            """Simple health check endpoint."""
            return {"status": "ok"}

    runtime_env = {"pip": ["silabs-mltk[full]==0.19.0"]}
    ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True, runtime_env=runtime_env)


    # Start the Serve instance and deploy
    serve.start(detached=True)
    serve.run(ImageClassifier.bind(), name="Image_Class", route_prefix="/ImClass")
    serve.delete("Test")  # placeholder removal


    print("Deployment completed. You can now send requests to your Ray Serve endpoint.")


if __name__ == "__main__":
    # - If you just want to test locally with a dummy model:

    model = keras.models.Sequential([
        keras.layers.Input(shape=(32, 32, 3)),
        keras.layers.Flatten(),
        keras.layers.Dense(10, activation='softmax')
    ])

    deploy(model, num_replicas=1)
    print("Deployment task ran locally.")
