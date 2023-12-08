from zenml import step
import ray
from typing import Annotated
import numpy as np
import tensorflow as tf


@step()
def retrain(train_images: np.ndarray, train_lables: np.ndarray, model: tf.keras.Sequential) \
        -> Annotated[tf.keras.Sequential, "Fashion model"]:
    @ray.remote(num_cpus=2)
    def fashion_retrain(x: np.ndarray, y: np.ndarray, mnist_model: tf.keras.Sequential) -> tf.keras.Sequential:
        batch_size = 128
        epochs = 1
        mnist_model.fit(x, y, batch_size=batch_size, epochs=epochs, validation_split=0.1)
        return mnist_model

    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)
    model.summary()
    model = fashion_retrain.remote(train_images, train_lables, model)
    model = ray.get(model)
    return model
