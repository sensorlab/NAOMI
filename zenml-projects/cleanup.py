import zenml
from zenml.client import Client
import os

# "Best-effort" cleanup, should be improved so that it deletes ALL pipelines not just latest and the ones named here

client = Client()

mnist_m = zenml.load_artifact("mnist_model")
fashion_m = zenml.load_artifact("Fashion model")


pipelines_to_delete = ["mnist_train", "fashion", "mnist_retraining", "fashion_retrain"]

for pipeline in pipelines_to_delete:
    try:
        client.delete_pipeline(pipeline)
    except KeyError:
        print(f"Can't delete pipeline {pipeline} that doesn't exist, proceeding...")

os.system("zenml artifact prune -y")

zenml.save_artifact(mnist_m, "mnist_model")
zenml.save_artifact(fashion_m, "Fashion model")
