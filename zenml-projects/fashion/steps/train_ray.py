from zenml import step
import ray
from typing import Any, Dict, Optional, Annotated
import numpy as np
import tensorflow as tf


@step()
def train(train_images: np.ndarray, train_lables: np.ndarray) -> Annotated[tf.keras.Sequential, "Fashion model"]:
    @ray.remote(num_cpus=4)
    def remo_train(train_images, train_lables):
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(512, activation=tf.nn.relu, input_shape=(784,)))
        model.add(tf.keras.layers.Dense(10, activation=tf.nn.softmax))

        model.compile(loss='categorical_crossentropy',
                      optimizer='rmsprop',
                      metrics=['accuracy'])

        model.summary()
        model.fit(train_images, train_lables, epochs=5)
        return model

    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)
    model = remo_train.remote(train_images, train_lables)
    model = ray.get(model)

    return model
