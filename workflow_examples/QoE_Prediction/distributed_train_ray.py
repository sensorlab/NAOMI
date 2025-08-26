from flytekit import task
import mlflow
# import mlflow.keras # deprecated
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
import s3fs
import pyarrow.fs
import numpy as np
import os
import pandas as pd

from .create_features import get_pod_template

# Get system ip from container environment variable set with pyflyte --env SYSTEM_IP=xxx
SYSTEM_IP = os.environ.get('SYSTEM_IP')

@task(pod_template=get_pod_template())
def train(data_url: str, epochs: int = 1, batch_size: int = 10) -> Sequential:
    import ray
    from ray import train, data
    from ray.train import ScalingConfig, RunConfig
    from ray.train.tensorflow import TensorflowTrainer
    from ray.train.tensorflow.keras import ReportCheckpointCallback
    def build_model() -> tf.keras.Model:
        model = Sequential()
        model.add(LSTM(units=150, activation="tanh", return_sequences=True, input_shape=input_shape))
        model.add(LSTM(units=150, return_sequences=True, activation="tanh"))
        model.add(LSTM(units=150, return_sequences=False, activation="tanh"))
        model.add((Dense(units=input_shape[1])))
        return model

    def train_func(config: dict):
        tf.keras.backend.clear_session()
        batch_size = config.get("batch_size", 10)
        epochs = config.get("epochs", 10)

        strategy = tf.distribute.MultiWorkerMirroredStrategy()
        with strategy.scope():
            multi_worker_model = build_model()
            multi_worker_model.compile(loss='mse', optimizer='adam', metrics=['mse'])

        dataset = ray.train.get_dataset_shard("train")

        results = []
        for _ in range(epochs):
            tf.keras.backend.clear_session()
            tf_dataset = dataset.to_tf(feature_columns='x', label_columns='y', batch_size=batch_size)
            history = multi_worker_model.fit(tf_dataset, callbacks=[ReportCheckpointCallback()])
            results.append(history.history)
        return results

    tf.config.threading.set_inter_op_parallelism_threads(4)

    ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True)

    s3_fs = s3fs.S3FileSystem(
        key='minio',
        secret='miniostorage',
        endpoint_url=f'http://{SYSTEM_IP}:30085',
        use_ssl="False"
    )

    with s3_fs.open(data_url, 'r') as f:
        df_new = pd.read_csv(f)
        x = np.array([np.fromstring(xi[1:-1], sep=' ').reshape(eval(shape)) for xi, shape in zip(df_new['x'], df_new['x_shape'])])
        y = np.array([np.fromstring(yi[1:-1], sep=' ').reshape(eval(shape)) for yi, shape in zip(df_new['y'], df_new['y_shape'])])

    input_shape = (x.shape[1], x.shape[2])
    # Create a DataFrame from x and y arrays
    df = pd.DataFrame({'x': list(x), 'y': list(y)})

    # Convert the DataFrame into a Ray dataset
    train_dataset = ray.data.from_pandas([df])

    custom_fs = pyarrow.fs.PyFileSystem(pyarrow.fs.FSSpecHandler(s3_fs))

    config = {"batch_size": batch_size, "epochs": 10}
    scaling_config = ScalingConfig(num_workers=4, use_gpu=False, trainer_resources={"CPU": 0}, resources_per_worker={"CPU": 4})
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
        model: Sequential = tf.keras.models.load_model(
            os.path.join(checkpoint_dir, "model.keras")
        )
        model.summary()
        mlflow.keras.log_model(model, artifact_path="models", registered_model_name="qoe_model_distributed")
        return model

