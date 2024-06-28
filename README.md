# Self-Evolving AI/ML Workflow System

AI/ML workflow solution is an MLOps system designed for deployment on a heterogeneous Kubernetes cluster with ARM and x86 GNU/Linux nodes, simulating distributed edge infrastructure common in RAN (Radio Access Networks), network slices and MEC (Multi-Access Edge Computing) devices.

The system leverages the Ray framework for data processing, model training, and model inference, distributing the computational load on edge and non-edge nodes. 
Data preparation can be done with frameworks like Pandas or Ray Data while using Minio as an object store. 
Model training, managed by Ray, supports Keras, TensorFlow, and PyTorch with minor modifications.
MLflow handles model storage and management, facilitating easy access and updates. 
Trained models are deployed as inference API endpoints using Ray Serve or as Kubernetes deployments using helm charts and docker containers.
Flyte orchestrates AI/ML workflows for retraining and redeployment of ML models, enabling retraining triggers based on monitored metrics. 
Prometheus and Grafana provide system monitoring. 

Developers register workflows with Flyte and monitor the system, while users can trigger workflows, monitor progress, and access models in MLflow. 
For example, in a RAN network, the system can enhance and control network operations through periodic metrics collection and automated retraining, ensuring up-to-date AI/ML assisted solutions. 
This system aims to run autonomously, delivering efficient production AI/ML workflows at the network edge.

The system is modular and can be adjusted to different use cases and requirements by enabling or disabling system components.

## Deployment

#### Minimal requirements
- 12 CPU cores
- 32GB RAM

#### Kubernetes cluster
- Install microk8s with addons: `dns`, `storage`, `ingress` or run install script `./helper_scripts/system-install.sh`
- (Optional) Run install script `./helper_scripts/rasp-install.sh` on any raspberry pi node you want to join to the cluster.

#### AI/ML workflow system
- Deploy with helm, adjust configs in `values_example.yaml`:

```bash
helm repo add semr_charts https://copandrej.github.io/Self-Evolving-AIML-Workflow/
helm install semr semr_charts/SEMR --values values_example.yaml
```

#### Environment
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

TODO

#### Dashboards
- Ray: `http://<node_ip>/ray/`
- Flyte: `http://<node_ip>:31082/`
- MinIO: `http://<node_ip>:30090/`
- Grafana: `http://<node_ip>:30000/`
- MLflow: `http://<node_ip>:31007/#/models`

## Repository structure

`workflow_examples/`
Examples of full MLOps pipelines

`helper_scripts/`
Install & configure scripts for the system

## System architecture

![arch](fig/arch.png)

## User workflow diagrams

![arch](fig/actor_workflow_diag.png)

![arch](fig/all_actors_workflow_diag.png)
