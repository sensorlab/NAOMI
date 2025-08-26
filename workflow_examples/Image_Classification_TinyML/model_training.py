from typing import Tuple
import os
import numpy as np

import mlflow
# import mlflow.keras

import tensorflow as tf
from tensorflow import keras
from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec
from flytekit import task, PodTemplate

# Model
from mltk.models.shared import ResNet10V1

SYSTEM_IP = os.environ.get('SYSTEM_IP')  # e.g. set with: pyflyte --env SYSTEM_IP=xxx


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
                            "memory": "4Gi",
                            "cpu": "1000m"
                        },
                        requests={
                            "memory": "2Gi"
                        }
                    ),
                ),
            ],
        )
    )


@task(pod_template=get_pod_template())
def train(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    epochs: int = 10,
    batch_size: int = 32
) -> any:
    """
    Train a ResNet-like model on the provided dataset using Ray,
    then log the model to MLflow and return the trained model object.
    """
    import ray

    # Define a Ray-remote function to do the actual training
    @ray.remote(num_cpus=2) # note that keras will always use all cpus in the container, so this is only for ray placement
    def ray_training(
        _x_train: np.ndarray,
        _y_train: np.ndarray,
        _x_test: np.ndarray,
        _y_test: np.ndarray,
        _epochs: int,
        _batch_size: int
    ) -> ResNet10V1:

        # Point MLflow to the tracking server
        mlflow.set_tracking_uri(f"http://{SYSTEM_IP}:31007")
        mlflow.set_experiment("Image classification")

        # Auto-log all Keras metrics, parameters, and model checkpoints
        mlflow.keras.autolog()

        # Define your model (ResNet10V1 in this example)
        model = ResNet10V1(
            input_shape=(32, 32, 3),
            num_classes=10
        )
        model.compile(
            loss='categorical_crossentropy',
            optimizer='adam',
            metrics=['accuracy']
        )
        model.summary()

        # Train the model
        model.fit(
            _x_train,
            _y_train,
            batch_size=_batch_size,
            epochs=_epochs,
            validation_data=(_x_test, _y_test),
            verbose=1
        )

        # Evaluate on the test set
        loss, acc = model.evaluate(_x_test, _y_test, verbose=0)
        print("Test Accuracy: ", acc)

        # Log the final metric:
        mlflow.log_metric("test_accuracy", acc)

        # Log the trained model to MLflow Model Registry
        mlflow.keras.log_model(
            model,
            artifact_path="models",
            registered_model_name="image_class_model"
        )

        return model

    runtime_env = {"pip": ["silabs-mltk[full]==0.19.0"]} # TO DO install the requirements in Ray image
    ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True, runtime_env=runtime_env)

    # Dispatch the remote training
    model_ref = ray_training.remote(x_train, y_train, x_test, y_test, epochs, batch_size)

    # Retrieve the trained model from Ray
    trained_model = ray.get(model_ref)

    return trained_model
if __name__ == "__main__":
    # For local debugging, pass in some dummy or real data
    # random data:
    x_train = np.random.randn(100, 32, 32, 3).astype('float32')
    y_train = keras.utils.to_categorical(np.random.randint(0, 10, size=(100,)), 10)
    x_test = np.random.randn(20, 32, 32, 3).astype('float32')
    y_test = keras.utils.to_categorical(np.random.randint(0, 10, size=(20,)), 10)

    model = train(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        epochs=1,
        batch_size=10
    )
    print("Training completed.")
