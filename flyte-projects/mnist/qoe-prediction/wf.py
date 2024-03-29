import typing
from . import train, deploy, fetch_data, test_deploy
from flytekit import workflow
import keras
from flytekit.core.node_creation import create_node

# Define your tasks and workflow using the @task and @workflow decorators
mnist_model = typing.NamedTuple("mnist_model", [("model", keras.Sequential)])


@workflow
def qoe_train() -> str:
    data = fetch_data()
    model_uri = train(x=data[0], y=data[1], epochs=1)
    dep = create_node(deploy, model=model_uri, num_replicas=1)
    test = create_node(test_deploy)
    dep >> test
    mnist_model(model=model_uri)
    return "Model Trained"



if __name__ == "__main__":
    print(f"Running wf() { qoe_train() }")
