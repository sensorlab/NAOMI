import logging
from flytekit import task, PodTemplate
import numpy as np
import keras
from typing import Tuple, Annotated, Dict, List
import ray
from ray import data

from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec
from flytekit import kwtypes
import os
import s3fs
import pyarrow.fs

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
def fetch_data() -> Tuple[
        Annotated[List[any], kwtypes(x_train=str)],
        Annotated[List[any], kwtypes(y_train=str)],
        Annotated[List[any], kwtypes(x_test=str)],
        Annotated[List[any], kwtypes(y_test=str)],]:

    s3_fs = s3fs.S3FileSystem(
        key='minio',
        secret='miniostorage',
        endpoint_url='http://193.2.205.27:30085',
        use_ssl="False"
    )
    custom_fs = pyarrow.fs.PyFileSystem(pyarrow.fs.FSSpecHandler(s3_fs))
    ray.init(address="ray://193.2.205.27:30001", ignore_reinit_error=True)

    @ray.remote
    def data_load(custom_fs):

        def scaling(batch):
            batch["image"] = batch["image"].astype("float32") / 255
            batch["image"] = np.expand_dims(batch["image"], -1)
            return batch

        def label(batch):
            temp = batch["path"]

            for ix, i in enumerate(temp):
                path_components = os.path.normpath(i).split(os.sep)
                temp[ix] = int(path_components[-2])

            temp = keras.utils.to_categorical(temp, 10)
            batch["path"] = temp
            return batch

        ds = ray.data.read_images(filesystem=custom_fs, include_paths=True, paths="s3://raybuck/MNIST_dataset/")
        ds = ds.map_batches(scaling, batch_format="numpy")
        ds = ds.map_batches(label, batch_format="numpy")

        train, test = ds.train_test_split(shuffle=True, test_size=0.15)
        return train.take(limit=5000), test.take(limit=750)

        

    train, test = ray.get(data_load.remote(custom_fs))
    x_train = [d["image"] for d in train if "image" in d]
    y_train = [d["path"] for d in train if "path" in d]
    x_test = [d["image"] for d in test if "image" in d]
    y_test = [d["path"] for d in test if "path" in d]

    return x_train, y_train, x_test, y_test
