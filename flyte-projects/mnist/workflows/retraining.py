import keras
from flytekit import task, PodTemplate
import ray
from typing import Annotated
import numpy as np
from kubernetes.client import V1PodSpec, V1Container, V1ResourceRequirements


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
                        "memory": "2Gi"
                    },
                    requests={
                        "memory": "2Gi"
                    }
                ),
            ),
        ],
    )
)
)
def retrain(x_train: np.ndarray, y_train: np.ndarray) \
        -> keras.Sequential:

    @ray.remote(num_cpus=2)
    def mnist_retraining(x: np.ndarray, y: np.ndarray):
        import mlflow.keras
        import keras
        mlflow.set_tracking_uri("http://193.2.205.27:5000")

        # Load the latest version of the model from MLFlow
        model_uri = "models:/mnist_model/latest"
        mnist_model: keras.Sequential = mlflow.keras.load_model(model_uri)

        # Re-train the model and store it back to mlflow
        mnist_model.fit(x, y, batch_size=128, epochs=1, validation_split=0.1)
        mlflow.keras.log_model(mnist_model, artifact_path="models", registered_model_name="mnist_model")

        return mnist_model

    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)
    model = mnist_retraining.remote(x_train, y_train)
    model = ray.get(model)
    return model
