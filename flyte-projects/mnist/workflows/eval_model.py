from typing import Annotated, List
import keras
from flytekit import task, PodTemplate
import numpy as np
import logging

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
def eval(model_uri: keras.Sequential, x_test: List[any], y_test: List[any]) -> float:
    model = model_uri
    score = model.evaluate(np.array(x_test), np.array(y_test), verbose=0)
    print("Test loss:", score[0])
    print("Test accuracy:", score[1])
    logging.info(f"Test loss: {score[0]}, Test accuracy: {score[1]}")
    return score[1]
