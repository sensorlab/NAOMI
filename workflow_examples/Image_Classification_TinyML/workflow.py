import typing
import keras
from flytekit import workflow
from flytekit.core.node_creation import create_node

from . import train, deploy, test_deploy, fetch_data_pd

image_classification_model = typing.NamedTuple(
    "image_classification_model",
    [("model", keras.Model)]
)

@workflow
def image_classification_workflow(
    batch_size: int = 10,
    epochs: int = 1
) -> str:
    """
    Orchestrate the entire image classification pipeline:
    1. Fetch data
    2. Train a model on that data
    3. Deploy the model via Ray Serve
    4. Test the deployed endpoint
    """
    # Step 1: Fetch Data
    x_train, y_train, x_test, y_test = fetch_data_pd()

    # Step 2: Train the Model
    trained_model = train(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        epochs=epochs,
        batch_size=batch_size
    )

    # Step 3: Deploy the Model
    deploy_node = create_node(
        deploy,
        model=trained_model,
        num_replicas=1
    )

    # Step 4: Test the Deployed Model
    test_node = create_node(test_deploy)

    # Chain: deploy -> test
    deploy_node >> test_node

    # Return something from the workflow
    return "Model trained and deployed successfully!"

if __name__ == "__main__":
    print(
        f"Running workflow: "
        f"{image_classification_workflow(bt_s=10, epochs=1)}"
    )
