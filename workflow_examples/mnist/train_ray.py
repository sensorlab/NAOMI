from typing import Annotated, List
from flytekit import task, PodTemplate
from kubernetes.client import V1PodSpec, V1Container, V1ResourceRequirements
import mlflow
import mlflow.keras
import ray
import tensorflow as tf
from ray import train, data
from ray.train import ScalingConfig, RunConfig
from ray.train.tensorflow import TensorflowTrainer
from ray.train.tensorflow.keras import ReportCheckpointCallback
import keras
from keras import layers
import s3fs
import pyarrow.fs
import numpy as np
import os


from .fetch import get_pod_template

# Get system ip from container environment variable set with pyflyte --env SYSTEM_IP=xxx
SYSTEM_IP = os.environ.get('SYSTEM_IP')

@task(pod_template=get_pod_template())
def train(train_ds: List[any]) -> keras.Sequential:
    def build_model() -> tf.keras.Model:
        model = keras.Sequential(
            [
                keras.Input(shape=(28, 28, 1)),
                layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
                layers.MaxPooling2D(pool_size=(2, 2)),
                layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
                layers.MaxPooling2D(pool_size=(2, 2)),
                layers.Flatten(),
                layers.Dropout(0.5),
                layers.Dense(10, activation="softmax"),
            ]
        )
        return model

    def train_func(config: dict):
        tf.keras.backend.clear_session()
        batch_size = config.get("batch_size", 128)
        epochs = config.get("epochs", 10)

        strategy = tf.distribute.MultiWorkerMirroredStrategy()
        with strategy.scope():
            # Model building/compiling need to be within `strategy.scope()`.
            multi_worker_model = build_model()
            multi_worker_model.compile(
                optimizer="adam",
                loss="categorical_crossentropy",
                metrics=["accuracy"]
            )

        dataset = ray.train.get_dataset_shard("train")

        results = []
        for _ in range(epochs):
            tf.keras.backend.clear_session()
            tf_dataset = dataset.to_tf(
                feature_columns="image", label_columns="path", batch_size=batch_size
            )
            history = multi_worker_model.fit(
                tf_dataset, callbacks=[ReportCheckpointCallback()]
            )
            results.append(history.history)
        return results

    ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True)

    s3_fs = s3fs.S3FileSystem(
        key='minio',
        secret='miniostorage',
        endpoint_url=f'http://{SYSTEM_IP}:30085',
        use_ssl="False"
    )

    custom_fs = pyarrow.fs.PyFileSystem(pyarrow.fs.FSSpecHandler(s3_fs))
    train_dataset = ray.data.from_items(train_ds)

    config = {"batch_size": 128, "epochs": 10}
    scaling_config = ScalingConfig(num_workers=2, use_gpu=False)
    run_config = RunConfig(storage_filesystem=custom_fs, storage_path="raybuck/training")

    trainer = TensorflowTrainer(
        train_loop_per_worker=train_func,
        train_loop_config=config,
        scaling_config=scaling_config,
        datasets={"train": train_dataset},
        run_config=run_config
    )

    result = trainer.fit()
    print(result.metrics)
    checkpoint = result.checkpoint

    mlflow.set_tracking_uri(f"http://{SYSTEM_IP}:31007")
    with checkpoint.as_directory() as checkpoint_dir:
        model: keras.Sequential = tf.keras.models.load_model(
            os.path.join(checkpoint_dir, "model.keras")
        )
        model.summary()
        mlflow.keras.log_model(model, artifact_path="models", registered_model_name="mnist_model_distributed")
        return model
