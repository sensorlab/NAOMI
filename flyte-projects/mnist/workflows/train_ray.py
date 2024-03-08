import keras
import ray
from typing import Annotated, List
import numpy as np
from flytekit import task, PodTemplate
from kubernetes.client import V1PodSpec, V1Container, V1ResourceRequirements


@task(pod_template=PodTemplate(
    pod_spec=V1PodSpec(
        node_selector={
            "kubernetes.io/arch": "amd64"
        },
        containers=[
            V1Container(
                name="primary",
                resources=V1ResourceRequirements(
                    limits={
                        "memory": "2Gi",
                        "cpu": "1000m"
                    },
                    requests={
                        "memory": "1Gi"
                    }
                ),
            ),
        ],
    )
)
)
def train(x_train: List[any], y_train: List[any]) \
        -> keras.Sequential:
    @ray.remote(num_cpus=2)
    def remo_train(x, y):
        import keras
        import ray
        from typing import Annotated
        import numpy as np
        import keras
        from keras import layers
        ## Uncomment for mlflow logging, make sure mlflow server is running on this ip
        import mlflow
        import mlflow.keras
        mlflow.set_tracking_uri("http://193.2.205.27:31007")
        # mlflow.set_experiment("mnist")
        mlflow.autolog()

        num_classes = 10
        input_shape = (28, 28, 1)

        model = keras.Sequential(
            [
                keras.Input(shape=input_shape),
                layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
                layers.MaxPooling2D(pool_size=(2, 2)),
                layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
                layers.MaxPooling2D(pool_size=(2, 2)),
                layers.Flatten(),
                layers.Dropout(0.5),
                layers.Dense(num_classes, activation="softmax"),
            ]
        )

        model.summary()

        batch_size = 128
        epochs = 5
        model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

        model.fit(x, y, batch_size=batch_size, epochs=epochs, validation_split=0.1)
        mlflow.keras.log_model(model, artifact_path="models", registered_model_name="mnist_model")
        return model

    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)
    model_uri = remo_train.remote(np.array(x_train), np.array(y_train))
    model_uri = ray.get(model_uri)
    return model_uri
