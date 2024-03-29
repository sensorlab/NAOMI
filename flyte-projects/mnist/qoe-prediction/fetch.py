from flytekit import task, PodTemplate
import numpy as np
from typing import Tuple, Annotated, List, Any
from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec
from flytekit import kwtypes
import s3fs
import pandas as pd
from numpy import ndarray, dtype


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
def fetch_data() -> tuple[ndarray[Any, dtype[Any]], ndarray[Any, dtype[Any]]]:

    # Create an S3 filesystem object
    s3_fs = s3fs.S3FileSystem(
        key='minio',
        secret='miniostorage',
        endpoint_url='http://193.2.205.27:30085',
        use_ssl=False  # Note: use_ssl should be False if your MinIO server is not using HTTPS
    )

    # Specify the path to the CSV file in MinIO
    file_path = 'raybuck/qoe_data/liveCell.csv'

    # Use pandas to read the CSV file directly from MinIO
    with s3_fs.open(file_path, 'rb') as f:
        full_df = pd.read_csv(f)

    features = full_df[['nrCellIdentity', 'pdcpBytesDl', 'pdcpBytesUl']]
    print("Dataframe:")
    print(features)

    features_cellc2b2 = features[features['nrCellIdentity'] == "c2/B2"]
    print("Dataframe for cell : c2/B2")
    print(features_cellc2b2)
    print('Previous Data Types are --> ', features_cellc2b2.dtypes)
    features_cellc2b2["pdcpBytesDl"] = pd.to_numeric(features_cellc2b2["pdcpBytesDl"], downcast="float")
    features_cellc2b2["pdcpBytesUl"] = pd.to_numeric(features_cellc2b2["pdcpBytesUl"], downcast="float")
    print('New Data Types are --> ', features_cellc2b2.dtypes)

    features_cellc2b2 = features_cellc2b2[['pdcpBytesDl', 'pdcpBytesUl']]

    def split_series(series, n_past, n_future):
        x, y = list(), list()
        for window_start in range(len(series)):
            past_end = window_start + n_past
            future_end = past_end + n_future
            if future_end > len(series):
                break
            # slicing the past and future parts of the window
            past, future = series[window_start:past_end, :], series[past_end:future_end, :]
            x.append(past)
            y.append(future)
        return np.array(x), np.array(y)

    x, y = split_series(features_cellc2b2.values, 10, 1)
    x = x.reshape((x.shape[0], x.shape[1], x.shape[2]))
    y = y.reshape((y.shape[0], y.shape[2]))
    print(x.shape)
    print(y.shape)

    return x, y
