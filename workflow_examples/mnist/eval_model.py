from typing import List
import keras
from flytekit import task
import numpy as np
import logging

from .fetch import get_pod_template

@task(pod_template=get_pod_template())
def eval(model_uri: keras.Sequential, x_test: List[any], y_test: List[any]) -> float:
    model = model_uri
    score = model.evaluate(np.array(x_test), np.array(y_test), verbose=0)
    print("Test loss:", score[0])
    print("Test accuracy:", score[1])
    logging.info(f"Test loss: {score[0]}, Test accuracy: {score[1]}")
    return score[1]
