import time
import requests
import os
import threading

"""
This is a proof of concept script that shows how retraining pipelines can be called from other programs.
"""

def test_inference(endpoint, image_pth) -> bool:
    with open(image_pth, "rb") as image_file:
        response = requests.post(f"http://193.2.205.27/{endpoint}", files={"file": image_file})

    response_json = response.json()
    return response_json["class_index"] == [5]


def run_test_inference(endpoint, script, image_pth):
    while test_inference(endpoint, image_pth):
        print(f"Testing inference for {endpoint} was successful. Running re-training again...")
        os.system(f"python {script}/run.py > /dev/null")
        print(f"Training {script} is done check the logs on ZenML. Now I am sleeping for 5min")
        time.sleep(300)
        print(f"Testing inference for {endpoint} again...")



# Create threads for each endpoint
thread1 = threading.Thread(target=run_test_inference, args=("ray-api/mnist/", "mnist", "my.png"))
# thread2 = threading.Thread(target=run_test_inference, args=("ray-api/fashion/", "fashion", "fashion.png"))

# Start the threads
print("Starting...")
thread1.start()
# thread2.start()
print("Running...")
thread1.join()
# thread2.join()
print("Inference didn't work correctly.")
