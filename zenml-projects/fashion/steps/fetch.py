from zenml import step
import numpy as np
import tensorflow as tf
from typing import Tuple, Annotated


@step
def fetch_data() -> Tuple[
    Annotated[np.ndarray, "train_images"],
    Annotated[np.ndarray, "train_labels"],
    Annotated[np.ndarray, "test_images"],
    Annotated[np.ndarray, "test_labels"],
]:
    (train_images, train_labels), (test_images, test_labels) = tf.keras.datasets.fashion_mnist.load_data()

    training_size = len(train_images)
    test_size = len(test_images)

    # Reshape from (N, 28, 28) to (N, 28*28=784)
    train_images = np.reshape(train_images, (training_size, 784))
    test_images = np.reshape(test_images, (test_size, 784))

    # Convert the array to float32 as opposed to uint8
    train_images = train_images.astype(np.float32)
    test_images = test_images.astype(np.float32)

    # Convert the pixel values from integers between 0 and 255 to floats between 0 and 1
    train_images /= 255
    test_images /= 255

    n_cat = 10
    train_labels = tf.keras.utils.to_categorical(train_labels, n_cat)
    test_labels = tf.keras.utils.to_categorical(test_labels, n_cat)

    return train_images, train_labels, test_images, test_labels
