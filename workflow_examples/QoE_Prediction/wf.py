import typing
from . import train, deploy, test_deploy, fetch_data_pd
from flytekit import workflow
import keras
from flytekit.core.node_creation import create_node

# Define your tasks and workflow using the @task and @workflow decorators
mnist_model = typing.NamedTuple("mnist_model", [("model", keras.Sequential)])


@workflow
def qoe_train(n: int = 1, bt_s: int = 10) -> str:
    data_url = fetch_data_pd(N=n)
    model_uri = train(data_url=data_url, epochs=1, batch_size=bt_s)
    dep = create_node(deploy, model=model_uri, num_replicas=1)
    test = create_node(test_deploy)
    dep >> test
    mnist_model(model=model_uri)
    return "Model Trained"



if __name__ == "__main__":
    print(f"Running wf() { qoe_train(N=1) }")
