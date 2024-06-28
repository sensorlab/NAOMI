# Self-Evolving AI/ML Workflow


#### Minimal requirements
- 12 CPU cores
- 32GB RAM

## Deployment

#### Kubernetes cluster
- Install microk8s with addons: 'dns', 'storage', 'ingress' or run install script `./helper_scripts/system-install.sh`
- (Optional) Run install script `./helper_scripts/rasp-install.sh` on any raspberry pi node you want to join to the cluster.

#### AI/ML workflow system
- Deploy with helm, adjust configs in `values_example.yaml`:

```bash
helm repo add semr_charts https://copandrej.github.io/Self-Evolving-AIML-Workflow/
helm install semr semr_charts/SEMR --values values_example.yaml
```

#### Environment
- Run config script `./helper_scripts/env-prepare.sh` on VM to install requirements and connect flytectl to the cluster for running AI/ML workflows.


## Usage

TODO

#### Dashboards
- Ray: `http://<node_ip>/ray/`
- Flyte: `http://<node_ip>:31082/`
- MinIO: `http://<node_ip>:30090/`
- Grafana: `http://<node_ip>:30000/`

## Repository structure

`workflow_examples/`
Examples of full MLOps pipelines

`helper_scripts/`
Install & configure scripts for the system
'

## System architecture

![arch](fig/arch.png)

## User workflow diagrams

![arch](fig/actor_workflow_diag.png)

![arch](fig/all_actors_workflow_diag.png)
