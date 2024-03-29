from typing import Annotated, List
from flytekit import task, PodTemplate
from kubernetes.client import V1PodSpec, V1Container, V1ResourceRequirements
import mlflow
import mlflow.keras
import ray
import keras
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
import numpy as np
from numpy import ndarray, dtype
from typing_extensions import Any

print("numpy version")
print(np.__version__)
import pandas as pd



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
def train(x: ndarray[Any, dtype[Any]], y:ndarray[Any, dtype[Any]], epochs: int) -> keras.Sequential:

    @ray.remote
    def ray_training(x, y, epochs: int):
        mlflow.set_tracking_uri("http://193.2.205.27:31007")
        mlflow.set_experiment("O-RAN qoe prediction service")
        mlflow.keras.autolog()

        model = Sequential()
        model.add(LSTM(units=150, activation="tanh", return_sequences=True, input_shape=(x.shape[1], x.shape[2])))
        model.add(LSTM(units=150, return_sequences=True, activation="tanh"))
        model.add(LSTM(units=150, return_sequences=False, activation="tanh"))
        model.add((Dense(units=x.shape[2])))

        model.compile(loss='mse', optimizer='adam', metrics=['mse'])
        model.summary()

        model.fit(x, y, batch_size=10, epochs=int(epochs), validation_split=0.2)
        yhat = model.predict(x, verbose=0)

        acc = np.mean(np.absolute(np.asarray(y) - np.asarray(yhat)) < 5)
        print("Accuracy: ", acc)
        mlflow.keras.log_model(model, artifact_path="models", registered_model_name="qoe_model")
        return model

    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)
    model = ray_training.remote(x, y, epochs)
    model = ray.get(model)
    return model
