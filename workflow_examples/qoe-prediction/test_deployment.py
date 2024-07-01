import logging
import requests
from flytekit import task


from .create_features import get_pod_template

@task(pod_template=get_pod_template())
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


    response = requests.post("http://193.2.205.63/ray-api/qoe/", json=data)
    response_json = response.json()
    logging.info(response_json)
    print(response_json)
