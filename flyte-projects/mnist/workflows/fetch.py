import logging
from flytekit import task, PodTemplate
import numpy as np
import keras
from typing import Tuple, Annotated, Dict
import ray
from ray import data

from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec
from flytekit import kwtypes


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
def fetch_data() -> Tuple[
        Annotated[np.ndarray, kwtypes(x_train=str)],
        Annotated[np.ndarray, kwtypes(y_train=str)],
        Annotated[np.ndarray, kwtypes(x_test=str)],
        Annotated[np.ndarray, kwtypes(y_test=str)],]:


    def scaling(batch):
        batch = batch.astype("float32") / 255
        return batch

    # Model / data parameters
    num_classes = 10
    input_shape = (28, 28, 1)
    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

    logging.info("Preprocessing data...")

    # Scale images to the [0, 1] range
    x_train = x_train.astype("float32") / 255
    x_test = x_test.astype("float32") / 255

    # Make sure images have shape (28, 28, 1)
    x_train = np.expand_dims(x_train, -1)
    x_test = np.expand_dims(x_test, -1)

    # convert class vectors to binary class matrices
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)

    logging.info("Done fetching data!")

    return x_train, y_train, x_test, y_test
