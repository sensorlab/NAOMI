from zenml import step
import ray
from typing import Any, Dict, Optional, Annotated
import numpy as np
import tensorflow as tf


@step()
def train(train_images: np.ndarray, train_lables: np.ndarray) -> Annotated[tf.keras.Sequential, "Fashion model"]:
    # in reality we would want to use ray jobs api to call ray code in a different file,
    # which would provide us with working dir,
    # functions that are defined outside of ray remote etc.
    @ray.remote(num_cpus=4)
    def remo_train(train_images, train_lables):
        import tensorflow as tf

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(512, activation=tf.nn.relu, input_shape=(784,)))
        model.add(tf.keras.layers.Dense(10, activation=tf.nn.softmax))

        # We will now compile and print out a summary of our model
        model.compile(loss='categorical_crossentropy',
                      optimizer='rmsprop',
                      metrics=['accuracy'])

        model.summary()
        model.fit(train_images, train_lables, epochs=5)
        return model

    ray.init(address="ray://193.2.205.27:10001", ignore_reinit_error=True)
    model = remo_train.remote(train_images, train_lables)
    model = ray.get(model)

    return model
