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
                        "memory": "1Gi"
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
def retrain(x_train: np.ndarray, y_train: np.ndarray, model: keras.Sequential) \
        -> keras.Sequential:

    @ray.remote(num_cpus=2)
    def mnist_retraining(x: np.ndarray, y: np.ndarray, mnist_model: keras.Sequential):
        # Re-train the model
        mnist_model.fit(x, y, batch_size=128, epochs=1, validation_split=0.1)
        return mnist_model

    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)
    model.summary()
    model = mnist_retraining.remote(x_train, y_train, model)
    model = ray.get(model)
    return model
