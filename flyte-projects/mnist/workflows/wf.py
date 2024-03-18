import typing
from typing import Tuple

from flytekit.core.condition import Condition
from flytekit.core.promise import Promise, VoidPromise

from . import train, deploy, eval, fetch_data, test_deploy, retrain, trigger_retraining
from flytekit import task, workflow, current_context, conditional
import keras
from flytekit.core.node_creation import create_node
from flytekit import LaunchPlan, CronSchedule

# Define your tasks and workflow using the @task and @workflow decorators
mnist_model = typing.NamedTuple("mnist_model", [("model", keras.Sequential)])


@workflow
def mnist_train() -> str:
    data = fetch_data()
    model_uri = train(train_ds=data[0])
    eval(model_uri=model_uri, x_test=data[1], y_test=data[2])

    dep = create_node(deploy, model=model_uri, num_replicas=1)
    test = create_node(test_deploy)
    dep >> test
    mnist_model(model=model_uri)
    return "Model Trained"


@workflow
def mnist_retraining() -> str:
    data = fetch_data()
    model_uri = retrain(train_ds=data[0])
    eval(model_uri=model_uri, x_test=data[1], y_test=data[2])

    dep = create_node(deploy, model=model_uri, num_replicas=1)
    test = create_node(test_deploy)
    dep >> test
    mnist_model(model=model_uri)
    return "Model Retrained"

@task()
def no_op() -> str:
    return "No retraining needed"

@workflow
def trigger_wf() -> str:
    drift_detected = trigger_retraining()
    return (conditional("Is model drift detected") # type:ignore
            .if_(drift_detected.is_true())
            .then(mnist_retraining())
            .else_()
            .then(no_op()))


fixed_rate_lp = LaunchPlan.get_or_create(
    name="Scheduled_MNIST_Retraining_trigger",
    workflow=trigger_wf,
    schedule=CronSchedule(schedule="*/30 * * * *")
)

# if __name__ == "__main__":
#     print(f"Running wf() { mnist_train() }")
