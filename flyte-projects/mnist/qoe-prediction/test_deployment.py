import logging
import os
import requests
from keras.datasets import mnist
from PIL import Image
from flytekit import task, PodTemplate
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
def test_deploy() -> None:
    data = {
        "signature_name": "serving_default",
        "instances":
            [[[2.56, 2.56],
            [2.56, 2.56],
            [2.56, 2.56],
            [2.56, 2.56],
            [2.56, 2.56],
            [2.56, 2.56],
            [2.56, 2.56],
            [2.56, 2.56],
            [2.56, 2.56],
            [2.56, 2.56]]]
    }


    response = requests.post("http://193.2.205.27/ray-api/qoe/", json=data)
    response_json = response.json()
    logging.info(response_json)
    print(response_json)
