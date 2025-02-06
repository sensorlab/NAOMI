import os
import numpy as np

import mlflow
import mlflow.keras
import ray
from ray import remote
from flytekit import task

import tensorflow as tf
from tensorflow import keras

from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec
from flytekit import PodTemplate

# If you want to use the MLTK MobileNetv1 architecture:
from mltk.models.shared import MobileNetV1 # this doesnt work as it uses keras 2.2

def get_pod_template():
    """Alternatively, import from data_extraction if desired."""
    return PodTemplate(
        pod_spec=V1PodSpec(
            node_selector={
                "kubernetes.io/arch": "amd64"
            },
            containers=[
                V1Container(
                    name="primary",
                    resources=V1ResourceRequirements(
                        limits={"memory": "4Gi", "cpu": "2000m"},
                        requests={"memory": "2Gi"}
                    ),
                ),
            ],
        )
    )


SYSTEM_IP = os.environ.get('SYSTEM_IP')


@task(pod_template=get_pod_template())
def train(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    epochs: int = 10,
    batch_size: int = 32
) -> keras.Model:
    """
    Train a MobileNetV1 model for Visual Wake Words classification (2 classes),
    log metrics to MLflow, and return the trained Keras model.
    """

    @ray.remote(num_cpus=2) # note that keras will always use all cpus in the container, so this is only for ray placement
    def ray_training(
        _x_train: np.ndarray,
        _y_train: np.ndarray,
        _x_test: np.ndarray,
        _y_test: np.ndarray,
        _epochs: int,
        _batch_size: int
    ):
        # Connect MLflow
        mlflow.set_tracking_uri(f"http://{SYSTEM_IP}:31007")
        mlflow.set_experiment("VisualWakeWords")
        mlflow.keras.autolog()

        model = MobileNetV1(
            input_shape=(96, 96, 3),  # 96x96, 3 channels
            num_classes=2
        )
        model.compile(
            loss='categorical_crossentropy',
            optimizer='adam',
            metrics=['accuracy']
        )
        model.summary()

        # Train
        model.fit(
            _x_train,
            _y_train,
            validation_data=(_x_test, _y_test),
            epochs=_epochs,
            batch_size=_batch_size,
            verbose=1
        )

        # Evaluate
        loss, acc = model.evaluate(_x_test, _y_test, verbose=0)
        print("Test Accuracy:", acc)
        mlflow.log_metric("test_accuracy", acc)

        # Log model to MLflow
        mlflow.keras.log_model(
            model,
            artifact_path="models",
            registered_model_name="vww_model"
        )

        return model

    runtime_env = {"pip": ["silabs-mltk[full]==0.19.0"]}
    # Initialize Ray (point to your Ray cluster)
    ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True, runtime_env=runtime_env)

    # Dispatch remote training
    model_ref = ray_training.remote(
        x_train, y_train, x_test, y_test, epochs, batch_size
    )
    trained_model = ray.get(model_ref)

    return trained_model


if __name__ == "__main__":
    # For local debug, mock small data
    x_mock = np.random.rand(10, 96, 96, 3).astype('float32')
    y_mock = tf.keras.utils.to_categorical(np.random.randint(2, size=(10,)), 2)
    x_mock_test = np.random.rand(2, 96, 96, 3).astype('float32')
    y_mock_test = tf.keras.utils.to_categorical(np.random.randint(2, size=(2,)), 2)

    m = train(x_mock, y_mock, x_mock_test, y_mock_test, epochs=1, batch_size=5)
    print("Model training complete.")
