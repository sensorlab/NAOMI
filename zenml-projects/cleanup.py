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

# kubernetes cleanup old pods
from kubernetes import client, config

config.load_kube_config()

# Create a client for the Core V1 API
v1 = client.CoreV1Api()

# Get a list of all pods in all namespaces
pods = v1.list_pod_for_all_namespaces().items
for pod in pods:
    if pod.status.phase in ['Succeeded', 'Failed']:
        v1.delete_namespaced_pod(pod.metadata.name, pod.metadata.namespace)
