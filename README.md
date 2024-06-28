# Self-Evolving AI/ML Workflow System

The Self-Evolving AI/ML Workflow System is a production MLOps solution designed for deployment on a heterogeneous Kubernetes cluster.

The system uses the Ray framework for data processing, model training, and inference, distributing the computational load across nodes.
Data preparation is done using Pandas or Ray Data, with Minio as an object store.
Model training supports Keras, TensorFlow, and PyTorch, and is managed by Ray. 

MLflow handles model storage and management, while trained models are deployed as inference API endpoints using Ray Serve or as Kubernetes deployments.
Flyte orchestrates AI/ML workflows for retraining and redeployment of models, with retraining triggers based on monitored metrics. 
System monitoring is provided by Prometheus and Grafana. 

Developers register workflows with Flyte and monitor the system, while users can trigger workflows, monitor progress, and access models in MLflow. 
The system is designed to run autonomously, delivering efficient production AI/ML workflows. 
It is modular and can be adjusted to different use cases and requirements.

## Deployment

#### Minimal requirements
- 12 CPU cores
- 32GB RAM

#### 1. Kubernetes cluster 
Skip this step if you already have a kubernetes cluster with required addons.
- Install microk8s with addons: `dns`, `storage`, `ingress` or run install script `./helper_scripts/system-install.sh`

- (Optional) Run install script `./helper_scripts/rasp-install.sh` on any raspberry pi node you want to join to the cluster.
- (Optional) Ansible playbook for installing microk8s on multiple nodes: `./helper_scripts/microk8s_ansible/` (requires ssh access and ansible)

#### 2. AI/ML workflow system
- Adjust configs in `values_example.yaml`, then deploy with helm:

```bash
helm repo add semr_charts https://copandrej.github.io/Self-Evolving-AIML-Workflow/
helm install semr semr_charts/SEMR --values values_example.yaml
```

#### 3. Environment
This step is only required for running example AI/ML workflows.
- Run config script `./helper_scripts/env-prepare.sh` on VM to install requirements and connect flytectl to the cluster for running AI/ML workflows.

## Configurations

All configurations are set as helm values. Adjust configs in `values_example.yaml` and deploy with helm.
Documentation and all configurations can be found in `SEMR/helm_charts/values.yaml`.

Project is modular with 5 main components:
- AI/ML model store with **MLflow**
- Distributed computing and AI/ML training with **Ray**
- Workflow orchestration with **Flyte**
- Data storage with **MinIO**
- System monitoring with **Prometheus & Grafana**

All components can be disabled, enabled, and configured in the helm values.

## Usage

After the system is deployed, users can access the components through the following dashboards.
System should be deployed in a closed network as access to dashboards and APIs is not secured.

#### Dashboards
- Ray: `http://<node_ip>/ray/`
- Flyte: `http://<node_ip>:31082/`
- MinIO: `http://<node_ip>:30090/`
- Grafana: `http://<node_ip>:30000/`
- MLflow: `http://<node_ip>:31007/#/models`

Components can be used separately or together to create AI/ML workflows.
To utilize MLflow model store users can use MLflow API on `http://<node_ip>:31007` (refer to MLflow documentation link: https://www.mlflow.org/docs/latest).
MinIO object store is accessible with default credentials `minio:miniostorage`.
Default grafana dashboard credentials are `admin:prom-operator`.
If required credentials can be changed in the helm values, other components and AI/ML workflow examples have to be updated with new credentials.
Ray cluster is a distributed computing framework and can be used with Ray API (https://docs.ray.io/en/master/index.html), refer to AI/ML workflow examples for how to send tasks to Ray cluster.
Flyte orchestrates AI/ML workflows. To create and run workflows refer to AI/ML workflow examples.


### AI/ML workflow examples

#### QoE prediction
TO-DO

#### MNIST
TO-DO

### Model deployment with SEMR_inference helm charts
TO-DO

## Repository structure

`workflow_examples/`
Examples of full MLOps workflows for QoE prediction and MNIST classification.

`helper_scripts/`
Install & configure scripts for kubernetes, distributed clusters and setting up the environment.

`docker_build/`
Dockerfiles and scripts for building docker images for model deployment (`docker_build/model_deployment/`) and for Ray cluster (`docker_build/ray_image/`).
If the system is deployed on multi architecture cluster, docker images have to be built for each architecture.

`helm_charts/`
Helm charts SEMR and SEMR_inference. 
SEMR is the main system helm chart, SEMR_inference is for model deployment.
Helm charts repository is hosted on GitHub pages: https://copandrej.github.io/Self-Evolving-AIML-Workflow/

`values_example.yaml`
Example of helm values file for configuring the system. 

## System architecture

![arch](fig/arch.png)

## User workflow diagrams

![arch](fig/actor_workflow_diag.png)

![arch](fig/all_actors_workflow_diag.png)
