import logging

import keras
from zenml import step
import ray
from typing import Any, Dict, Optional
import numpy as np
import mlflow.keras

 
@step(enable_cache=True)
def train(x_train: np.ndarray, y_train: np.ndarray) -> keras.Sequential:
    @ray.remote(num_cpus=4)
    def remo_train(x, y):
        import keras
        from keras import layers
        import mlflow
        import numpy as np
        import mlflow.keras

        mlflow.set_tracking_uri("http://193.2.205.27:5000")
        mlflow.set_experiment("mnist")
        mlflow.autolog()

        num_classes = 10
        input_shape = (28, 28, 1)

        model = keras.Sequential(
            [
                keras.Input(shape=input_shape),
                layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
                layers.MaxPooling2D(pool_size=(2, 2)),
                layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
                layers.MaxPooling2D(pool_size=(2, 2)),
                layers.Flatten(),
                layers.Dropout(0.5),
                layers.Dense(num_classes, activation="softmax"),
            ]
        )

        model.summary()

        """
        ## Train the model
        """

        batch_size = 128
        epochs = 1

        model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

        model.fit(x, y, batch_size=batch_size, epochs=epochs, validation_split=0.1)

        # mlflow.keras.log_model(model, "model")
        # get model uri
        # model_uri = mlflow.get_artifact_uri("model")
        return model

    ray.init(address="ray://193.2.205.27:10001")
    model_uri = remo_train.remote(x_train, y_train)
    model_uri = ray.get(model_uri)
    # mlflow.keras.log_model(model_uri, "mnist")
    return model_uri
