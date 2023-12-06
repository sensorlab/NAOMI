import logging
from zenml import step
import numpy as np
import keras
from typing import Tuple

@step
def fetch_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # Model / data parameters
    num_classes = 10
    input_shape = (28, 28, 1)

    logging.info("Fetching data...")
    # Load the data and split it between train and test sets
    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

    logging.info("Preprocessing data...")

    # Scale images to the [0, 1] range
    x_train = x_train.astype("float32") / 255
    x_test = x_test.astype("float32") / 255
    
    # Make sure images have shape (28, 28, 1)
    x_train = np.expand_dims(x_train, -1)
    x_test = np.expand_dims(x_test, -1)

    # convert class vectors to binary class matrices
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)
    
    logging.info("Done fetching data!")
    
    return x_train, y_train, x_test, y_test
