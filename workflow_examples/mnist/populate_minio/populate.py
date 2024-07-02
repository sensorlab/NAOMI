import os
import tarfile
from minio import Minio

# Create a MinIO client
client = Minio(
    "<CHANGE-ME>:30085",
    access_key="minio",
    secret_key="miniostorage",
    secure=False
)

# Specify the dataset and the bucket name
local_file = "MNIST_dataset.tar.xz"
bucket_name = "raybuck"

# Extract the tar.xz file to a directory
with tarfile.open(local_file, "r:xz") as tar:
    tar.extractall()

# The name of the directory is assumed to be the same as the name of the tar.xz file without the extension
local_directory = local_file.rsplit('.', 2)[0]

# Iterate over each file in the local directory
for root, dirs, files in os.walk(local_directory):
    for file in files:
        # Construct the local file path
        local_file_path = os.path.join(root, file)

        # Construct the object name in the bucket
        object_name = os.path.join(local_directory, os.path.relpath(local_file_path, local_directory))
        # Upload the file to the bucket
        client.fput_object(bucket_name, object_name, local_file_path)
