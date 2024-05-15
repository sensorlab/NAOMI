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
def fetch_data_pd(N: int) -> str:

    # Create an S3 filesystem object
    s3_fs = s3fs.S3FileSystem(
        key='minio',
        secret='miniostorage',
        endpoint_url='http://193.2.205.63:30085',
        use_ssl=False  # Note: use_ssl should be False if your MinIO server is not using HTTPS
    )

    # Specify the path to the CSV file in MinIO
    file_path = f'raybuck/qoe_data/liveCell-x{N}.csv'

    # Use pandas to read the CSV file directly from MinIO
    with s3_fs.open(file_path, 'rb') as f:
        df = pd.read_csv(f)

    # Select the required columns
    df = df[['nrCellIdentity', 'pdcpBytesDl', 'pdcpBytesUl']]

    # Filter the data
    df = df[df['nrCellIdentity'] == "c2/B2"]

    # Convert the data types
    df["pdcpBytesDl"] = pd.to_numeric(df["pdcpBytesDl"], downcast="float")
    df["pdcpBytesUl"] = pd.to_numeric(df["pdcpBytesUl"], downcast="float")

    # Select the required columns
    df = df[['pdcpBytesDl', 'pdcpBytesUl']]

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

    x, y = split_series(df.values, 10, 1)
    x = x.reshape((x.shape[0], x.shape[1], x.shape[2]))
    y = y.reshape((y.shape[0], y.shape[2]))
    print(x.shape)
    print(y.shape)

    x_shapes = [str(xi.shape) for xi in x]  # Store the original shapes
    y_shapes = [str(yi.shape) for yi in y]  # Store the original shapes
    x = x.reshape((x.shape[0], -1))  # Flatten the arrays
    y = y.reshape((y.shape[0], -1))  # Flatten the arrays
    df_new = pd.DataFrame({'x': list(x), 'y': list(y), 'x_shape': x_shapes, 'y_shape': y_shapes})

    features_url = f'raybuck/qoe_data/features-x{N}.csv'
    # Write the result to a new CSV file
    with s3_fs.open(features_url, 'w') as f:
        df_new.to_csv(f, index=False)

    return features_url


if __name__ == "__main__":
    fetch_data_pd(N=10)
