import typing
import keras
from flytekit import workflow
from flytekit.core.node_creation import create_node

# Import tasks from the files above
from .data_extraction import fetch_data_vww
from .model_training import train
from .model_deployment import deploy
from .test_deployment import test_deploy


vww_model_type = typing.NamedTuple("vww_model_type", [("model", keras.Model)])


@workflow
def visual_wake_words_workflow(
    batch_size: int = 32,
    epochs: int = 5,
    test_split: float = 0.1
) -> str:
    """
    Orchestrate the entire Visual Wake Words pipeline:
      1. Fetch data
      2. Train a MobileNetV1 model
      3. Deploy the model
      4. Test the deployed service
    """

    # Step 1: Fetch data
    x_train, y_train, x_test, y_test = fetch_data_vww(test_size=test_split)

    # Step 2: Train the model
    trained_model = train(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        epochs=epochs,
        batch_size=batch_size
    )

    # Step 3: Deploy the trained model
    dep_node = create_node(
        deploy,
        model=trained_model,
        num_replicas=1
    )

    # Step 4: Test the deployed service
    test_node = create_node(test_deploy)

    # Ensure test runs after deployment
    dep_node >> test_node

    return "Model trained and deployed successfully!"


if __name__ == "__main__":
    print("Running Visual Wake Words workflow locally...")
    result_str = visual_wake_words_workflow(
        batch_size=16,
        epochs=1,      # For a quick test
        test_split=0.1
    )
    print(result_str)
