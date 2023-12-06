import tensorflow as tf
from zenml import step
import numpy as np
from typing import Annotated


@step
def eval(model_uri: tf.keras.Sequential, test_images: np.ndarray, test_lables: np.ndarray)\
        -> Annotated[float, "Accuracy"]:
    model = model_uri
    score = model.evaluate(test_images, test_lables)
    print("Test loss:", score[0])
    print("Test accuracy:", score[1])
    return score[1]
