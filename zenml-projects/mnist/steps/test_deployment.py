import logging
import os
import requests
from keras.datasets import mnist
from PIL import Image
from zenml import step

@step()
def test_deploy() -> None:
    # Load the MNIST dataset and select an image
    img_array = mnist.load_data()[0][0][0]

    # Save the image to a file
    Image.fromarray(img_array).save('my.png')

    # Send a POST request with the image file
    with open("my.png", "rb") as image_file:
        response = requests.post("http://193.2.205.27/ray-api/mnist/", files={"file": image_file})

    # Log the response and check if the test passed
    response_json = response.json()
    logging.info(response_json)
    assert response_json["class_index"] == [5], "Test failed!"

    # Remove the image file
    os.remove('my.png')
