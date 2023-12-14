import typing
from flytekit import workflow
from kubernetes.client import V1Container, V1ResourceRequirements

from . import train, deploy, eval, fetch_data, test_deploy, retrain
from flytekit import task, workflow, current_context

from flytekit.core.node_creation import create_node

# Define your tasks and workflow using the @task and @workflow decorators

@workflow
def mnist_train():
    data = fetch_data()
    model_uri = train(x_train=data[0], y_train=data[1])
    eval(model_uri=model_uri, x_test=data[2], y_test=data[3])

    dep = create_node(deploy, model=model_uri)
    test = create_node(test_deploy)
    dep >> test



if __name__ == "__main__":
    print(f"Running wf() { mnist_train() }")
