from typing import Tuple
import os
import numpy as np
from tensorflow.keras.utils import to_categorical
from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec
from flytekit import task, PodTemplate
from tensorflow.keras.datasets import cifar10


# PodTemplate is a way to specify the resources needed to run a task in a Kubernetes cluster.
# It is not needed, if not specified, Flyte will use the default resources specified in values_example.yaml
# It might be needed if you are running a heterogeneous cluster so you specify the node_selector
# as for some reason this is not supported through Flyte helm values.
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
def fetch_data_pd() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Fetch and preprocess the CIFAR10 dataset.
    Returns:
        x_train, y_train, x_test, y_test
    """
    # Load the CIFAR10 dataset
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    # Convert to float32 for scaling
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')

    # Example: Scale to range ~[-1, 1]
    x_train = (x_train - 128.0) / 128.0
    x_test = (x_test - 128.0) / 128.0

    # Convert labels to one-hot encoding
    y_train = to_categorical(y_train, 10)
    y_test = to_categorical(y_test, 10)

    return x_train, y_train, x_test, y_test


if __name__ == "__main__":
    # Just run the task standalone (for debugging or local testing)
    x_train, y_train, x_test, y_test = fetch_data_pd()
    print('Train images shape:', x_train.shape)
    print('Train labels shape:', y_train.shape)
    print('Test images shape:', x_test.shape)
    print('Test labels shape:', y_test.shape)
