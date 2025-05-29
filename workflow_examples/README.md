# Adapting Your ML Code to NAOMI Using QoE Example

This guide shows how to adapt your ML code to run on NAOMI by following the QoE Prediction workflow example. 

We use QoE example (`workflow_examples/QoE_Prediction/`) as a template. You'll adapt your ML code to match its structure, replacing QoE's model with your own while keeping same workflow organization.

You'll need:
1. Your existing ML code
2. NAOMI deployed on Kubernetes cluster (see main README)

The guide shows how to:
1. Structure your code like QoE example
2. Use Ray for training
3. Deploy model as an API endpoint
4. Manage the workflow with Flyte
5. Optionally use MinIO for data storage and MLflow for model management

## QoE Example Structure

The QoE workflow is organized as:
```
QoE_Prediction/
├── __init__.py            # To make it a package (adjust as needed)    
├── create_features.py     # Data preprocessing
├── train_ray.py           # Model training with Ray
├── deploy_model.py        # Model serving with Ray Serve
├── test_deployment.py     # API testing (optional)
├── wf.py                  # Workflow definition
└── populate_minio/        # Data ingestion (optional)
    └── insert.py
```

Each component has a specific role in the workflow and runs in a separate Flyte task as Kubernetes pod:
1. Data preprocessing and feature creation
2. Model training on Ray cluster
3. Model deployment as API endpoint
4. Workflow orchestration with Flyte

## Step 1: Flyte Templates

1. Create or copy the same directory structure as the example workflow.


2. Resource template for flyte tasks, adjust if needed. Defaults will work for most use cases (see create_features.py). This template will be used for all flyte tasks:

```python
from flytekit import PodTemplate
from kubernetes.client import V1ResourceRequirements, V1Container, V1PodSpec

def get_pod_template():
    return PodTemplate(
        pod_spec=V1PodSpec(
            node_selector={"kubernetes.io/arch": "amd64"},
            containers=[
                V1Container(
                    name="primary",
                    resources=V1ResourceRequirements(
                        limits={"memory": "2Gi", "cpu": "1000m"},
                        requests={"memory": "1Gi"}
                    ),
                ),
            ],
        )
    )
```

## Step 2: Data Preprocessing

1. Example data preprocessing task (create_features.py):

```python
from flytekit import task
from .create_features import get_pod_template

@task(pod_template=get_pod_template())
def preprocess_data(input_path: str) -> pd.DataFrame:
    # Your data loading code here
    data = load_your_data(input_path)
    
    # Your preprocessing steps
    processed_data = #...
    
    return processed_data
```

Note: If you want to use MinIO for data storage like QoE example, see [MinIO Integration](#minio-for-data-storage) section. We load the data and then store it in MinIO for next tasks. Both approaches are valid. For larger datasets we recommend using MinIO as cached data in Flyte can get very large.

## Step 3: Model Training with Ray

Replace our example model with your model in train_ray.py. Here you can also adjust the parameters for Ray, such as number of CPUs, memory, etc. For more information refer to Ray docs. Note that we use SYSTEM_IP environment variable to connect to Ray cluster, which is set when executing the workflow later. The arguments to flyte task train can be set when running the flyte workflow so you can control the number of epochs, batch size. This can be useful for automation. Add parameters to flyte tasks if needed. 


```python
from flytekit import task
import ray
from .create_features import get_pod_template # takes the pod template from create_features.py
import os

@task(pod_template=get_pod_template())
def train(data: pd.DataFrame, epochs: int = 1) -> Any:
    # Connect to NAOMI Ray (required)
    ray.init(
        address=f"ray://{os.environ.get('SYSTEM_IP')}:30001",
        ignore_reinit_error=True
    )

    # Define remote training function and configure Ray resources
    @ray.remote(num_cpus=1)
    def ray_training(data, epochs):
        # Replace with your model creation/training code
        model = create_your_model()
        model.fit(data, epochs=epochs)
        
        # Optional: Log model to MLflow
        # See MLflow Integration section below
        return model

    # Execute training on Ray cluster
    model = ray_training.remote(data, epochs)
    model = ray.get(model)
    return model
```

For distributed training options and more configurations, see [Ray documentation](https://docs.ray.io/en/latest/train/train.html).

We can also store the model to MLFlow if needed. See [MLflow Integration](#mlflow-integration) section for details on how to log and load models with MLflow during the training task.

In some cases you might need to add aditional dependencies to Ray cluster. It should already cover most of the ML use cases however if something specific is needed you can add them to Ray init configuration. For example we had to do this for our TinyML examples. If you need to install additional Python packages, you can do it like this. 

```python
runtime_env = {"pip": ["silabs-mltk[full]==0.19.0"]}
ray.init(address=f"ray://{SYSTEM_IP}:30001", ignore_reinit_error=True, runtime_env=runtime_env)
```

## Step 4: Model Deployment

Adapt the QoE deployment for your model (deploy_model.py). This will deploy the model on Ray Serve as an API endpoint. You can adjust parameters to control the number of replicas for your model server. This is useful for scaling based on your model's load. Many more configurations are available in Ray Serve documentation. 

```python
from fastapi import FastAPI
import ray
from ray import serve
from flytekit import task
from .create_features import get_pod_template

@task(pod_template=get_pod_template())
def deploy(model: Any, max_replicas: int) -> None:
    app = FastAPI()

    @serve.deployment(
        name="your_model",
        max_ongoing_requests=2000,
        ray_actor_options={"num_cpus": 1, "num_gpus": 0},
        autoscaling_config={
            "min_replicas": 1,
            "max_replicas": max_replicas
        }

    )
    @serve.ingress(app)
    class ModelServer:
        def __init__(self):
            self.model = model # load the model passed from the training task or from MLflow

        @app.post("/")
        async def predict(self, data: dict):
            # Adapt input/output format for your model
            result = self.model.predict(data)
            return {"prediction": str(result)}

    ray.init(address=f"ray://{os.environ.get('SYSTEM_IP')}:30001")
    serve.run(ModelServer.bind())
    serve.delete("Test")  # Placeholder removal 
```

Again if your model is stored in MLflow, you can load it in the deploy task. See [MLflow Integration](#mlflow-integration) section.

## Step 5: Define Workflow

Connect everything in wf.py. Arguments to the workflow can be set when running the workflow. Dependencies between tasks are defined using the `create_node` function, which allows you to chain tasks together. Feel free to change the workflow. This workflow will create the following DAG:
```
preprocess_data -> train -> deploy -> test_deploy
```


```python
from flytekit import workflow
from . import train, deploy, test_deploy
from flytekit.core.node_creation import create_node

@workflow
def training_workflow(
    input_path: str,
    epochs: int = 1,
    max_replicas: int = 1
) -> str:
    # Run preprocessing and training
    data = preprocess_data(input_path)
    model = train(data=data, epochs=epochs)
    
    # Deploy model
    deploy_node = create_node(
        deploy,
        model=model,
        max_replicas=max_replicas
    )
    test_node = create_node(test_deploy)
    deploy_node >> test_node
    
    return "Workflow Complete"
```
Make sure to adjust __init__.py to include any new tasks. See the QoE example for details. This takes some trial and error as Flyte packaging works slightly different.

## Step 6: Build and Deploy

Next step is to build the Docker image for your workflow and run it on NAOMI. This involves creating a Dockerfile, building the image, and pushing it to your container registry. All our examples use the same template for this process. However feel free to copy docker_build.sh and Dockerfile and requirements.txt from the workflow_examples directory to your own project directory.

### 1. Setup Requirements

Adjust requirements.txt with all dependencies for your ML code. See the requirements from our examples as a template. Core requirements for NAOMI should not be removed. (Ray, FastAPI, mlflow, flytekit, pillow, s3fs, kubernetes)

### 2. Docker Image

Adjust Dockerfile if needed, however the default should work for most cases. 


The example build script expects:
- Your project name (e.g., `your_workflow`), this will be used as the image name.
- Docker registry URL (e.g. your online docker registry)
- Version tag

```bash
# From workflow_examples directory
./docker_build.sh \
    -p your_workflow \
    -r your_registry \
    -v 1

```
Push the image to your registry. This image will be used to run the workflow on NAOMI using pyflyte later.

### 4. Run Workflow

We use pyflyte to run the image on NAOMI. We set up the SYSTEM_IP environment variable automatically. Change the image name to match your built image. Change the name of the workflow and add arguments that are defined in the workflow as parameters.

```bash
pyflyte run --remote \
    --env SYSTEM_IP=$(hostname -I | awk '{print $1}') \
    --image your_registry/your_workflow:1 \
    wf.py training_workflow \
    --epochs 10
```
Monitor the execution on NAOMI dashboards.

## System Access

Useful API endpoints and dashboards for NAOMI:

- Ray API: `ray://{SYSTEM_IP}:30001`
- Ray Dashboard: `http://{SYSTEM_IP}/ray/`
- Flyte Dashboard: `http://{SYSTEM_IP}:31082`
- Grafana Dashboard: `http://{SYSTEM_IP}:30000` (credentials: admin/prom-operator)
- Prometheus: `http://{SYSTEM_IP}:30002`
- MinIO: `http://{SYSTEM_IP}:30090` (credentials: minio/miniostorage)
- MinIO API: `http://{SYSTEM_IP}:30085`
- MLflow API: `http://{SYSTEM_IP}:31007`
- MLflow Dashboard: `http://{SYSTEM_IP}:31007/#/`


## Optional Integrations

### MinIO for Data Storage

Access MinIO at `http://{SYSTEM_IP}:30090` (credentials: minio/miniostorage)
API is available at `http://{SYSTEM_IP}:30085`
We suggest reading the documentation. For simple use case with csv data see below and our QoE example.

1. Upload data:
```python
from minio import Minio
from io import StringIO, BytesIO

# credentials for MinIO
MINIO_ENDPOINT = '<change_me>:30085'
MINIO_ACCESS_KEY = 'minio'
MINIO_SECRET_KEY = 'miniostorage'
MINIO_BUCKET_NAME = 'your_bucket_name' 

class INSERTDATA:
    def __init__(self):
        self.minio_client = Minio(MINIO_ENDPOINT,
                                  access_key=MINIO_ACCESS_KEY,
                                  secret_key=MINIO_SECRET_KEY,
                                  secure=False)  # Change to True if using HTTPS

db = INSERTDATA()
csv_bytes = BytesIO(csv_data.encode('utf-8'))
db.minio_client.put_object(MINIO_BUCKET_NAME, f'folder/your_data.csv', csv_bytes, len(csv_data))
```

2. Read data:
```python
import s3fs

def read_data(file_path: str) -> pd.DataFrame:
    s3_fs = s3fs.S3FileSystem(
        key='minio',
        secret='miniostorage',
        endpoint_url=f'http://{os.environ.get("SYSTEM_IP")}:30085',
        use_ssl=False
    )
    
    file_path = f'your_bucket_name/folder/data.csv'


    with s3_fs.open(file_path, 'r') as f:
        return pd.read_csv(f)
```

### MLflow Integration

Access MLflow API at `http://{SYSTEM_IP}:31007`
Dashboard at `http://{SYSTEM_IP}:31007/#/`

1. In your training task:
```python
import mlflow


mlflow.set_tracking_uri(f"http://{os.environ.get('SYSTEM_IP')}:31007")
mlflow.set_experiment("your-experiment")

# For keras you can use

mlflow.keras.autolog()

# Or one option is to use:

with mlflow.start_run():
    # Train your model
    model = train_model(data, epochs)
    
    # Log metrics
    mlflow.log_metric("accuracy", accuracy)
    
    # Save model
    mlflow.keras.log_model(
        model,
        "model",
        registered_model_name="your_model"
    )
        

```

2. Load saved model:
```python

mlflow.set_tracking_uri(f"http://{os.environ.get('SYSTEM_IP')}:31007")
model_uri = f"models:/{name}/{version}"
model = mlflow.keras.load_model(model_uri) # adjust for your model type

```

For more examples, check the QoE and other workflows in the `workflow_examples` directory.
