import os
import numpy as np
import tensorflow as tf
from flytekit import task, PodTemplate
from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec

from mltk.utils.archive_downloader import download_verify_extract
from glob import glob
from sklearn.model_selection import train_test_split


def get_pod_template():
    """Return a PodTemplate for consistent resource usage across tasks."""
    return PodTemplate(
        pod_spec=V1PodSpec(
            node_selector={
                "kubernetes.io/arch": "amd64"
            },
            containers=[
                V1Container(
                    name="primary",
                    resources=V1ResourceRequirements(
                        limits={
                            "memory": "4Gi",
                            "cpu": "2000m"
                        },
                        requests={
                            "memory": "2Gi"
                        }
                    ),
                ),
            ],
        )
    )


# The MLTK function that downloads and verifies the dataset
def download_vww_dataset() -> str:
    """
    Download the Visual Wake Words dataset from MLTK's public archive
    and extract it to a local directory. Returns the path to the dataset.
    """
    dataset_dir = download_verify_extract(
        url='https://www.silabs.com/public/files/github/machine_learning/benchmarks/datasets/vw_coco2014_96.tar.gz',
        dest_subdir='datasets/mscoco14/preprocessed/v1',
        file_hash='A5A465082D3F396407F8B5ABAF824DD5B28439C4',
        show_progress=True,
        remove_root_dir=True
    )
    return dataset_dir


@task(pod_template=get_pod_template())
def fetch_data_vww(
    test_size: float = 0.1
) -> (np.ndarray, np.ndarray, np.ndarray, np.ndarray):
    """
    1) Download the Visual Wake Words dataset
    2) Recursively load images from 'person' and 'non_person' subdirectories
    3) Split into train & test sets (by default, 90%/10%)
    4) Return (x_train, y_train, x_test, y_test) as float32 arrays
    """

    dataset_dir = download_vww_dataset()
    # The dataset has subfolders 'person' and 'non_person'.

    person_dir = os.path.join(dataset_dir, "person")
    non_person_dir = os.path.join(dataset_dir, "non_person")

    person_images = glob(os.path.join(person_dir, "*.jpg"))
    non_person_images = glob(os.path.join(non_person_dir, "*.jpg"))

    print(f"Found {len(person_images)} person images.")
    print(f"Found {len(non_person_images)} non_person images.")

    X = []
    Y = []

    # Load person images (limit to 5 000 out of cca 50 000)
    for img_path in person_images[:5000]:
        img = tf.keras.utils.load_img(img_path, target_size=(96, 96))
        img_array = tf.keras.utils.img_to_array(img)  # shape (96,96,3)
        X.append(img_array)
        Y.append(1)  # label = 1 for "person"

    # Load non_person images (limit to 5 000 out of cca 50 000)
    for img_path in non_person_images[:5000]:
        img = tf.keras.utils.load_img(img_path, target_size=(96, 96))
        img_array = tf.keras.utils.img_to_array(img)
        X.append(img_array)
        Y.append(0)  # label = 0 for "non_person"

    # Convert lists to numpy arrays
    X = np.array(X, dtype=np.float32)
    Y = np.array(Y, dtype=np.float32)

    # Scale the images from [0..255] to [-1..1], e.g.:
    X = (X - 128.0) / 128.0

    # Convert labels to one-hot for 2 classes: shape => (N, 2)
    Y = tf.keras.utils.to_categorical(Y, num_classes=2)

    print("Loaded dataset shape:", X.shape, Y.shape)

    # Split into train/test
    x_train, x_test, y_train, y_test = train_test_split(
        X, Y, test_size=test_size, random_state=42, shuffle=True
    )

    print("Train set:", x_train.shape, y_train.shape)
    print("Test set: ", x_test.shape, y_test.shape)

    return x_train, y_train, x_test, y_test


if __name__ == "__main__":
    # Quick test: call the fetch_data_vww function
    x_train, y_train, x_test, y_test = fetch_data_vww()
    print("Data fetching complete.")
