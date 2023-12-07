import time
import requests
import os


def test_inference() -> bool:
    with open("my.png", "rb") as image_file:
        response = requests.post("http://193.2.205.27/ray-api/mnist/", files={"file": image_file})

    response_json = response.json()
    return response_json["class_index"] == [5]


def run_test_inference():
    while test_inference():
        print("Testing inference for mnist was successful. Running re-training again...")
        os.system("python mnist/run.py --retrain > /dev/null")
        print("Training mnist is done check the logs on ZenML. Now I am sleeping for 5min")
        time.sleep(300)
        print("Testing inference for mnist again...")


print("Starting...")
run_test_inference()
print("Inference didn't work correctly.")
