import keras
from zenml import step
import numpy as np
import logging


@step
def eval(model_uri: keras.Sequential, x_test: np.ndarray, y_test: np.ndarray) -> list:
    model = model_uri
    score = model.evaluate(x_test, y_test, verbose=0)
    print("Test loss:", score[0])
    print("Test accuracy:", score[1])
    logging.info(f"Test loss: {score[0]}, Test accuracy: {score[1]}")
    return score
