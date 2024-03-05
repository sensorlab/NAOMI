# Self-Evolving AI/ML Workflow

Our system is managed by ArgoCD, all changes to conf/kube_conf will be picked up by Argo and can be synced manually or automatically to our cluster.

### To recreate our system:
- Use at least one node with Ubuntu installed (Tested with 22.04.1-Ubuntu).
- Clone the repo.
- Run install script `./scripts/system-install.sh` which installs microk8s and argocd and automatically deploys all our apps on the cluster.
- (Optional) Run install script `scripts/rasp-install.sh` on any raspberry pi node you want to join to the cluster.
- Run config script `./scripts/env-prepare.sh` on VM to connect to zenml instance and prepare VM env for running pipelines. This can be run from a different machine (Not tested).

> Scripts should be run from root of repository.
> For scripts to work entire conf/ folder needs to be included
> If any of the scripts fail, they should be run line by line to debug the problem.

### In short:
```bash
git clone https://github.com/copandrej/IJS-AI_orchestration.git && cd IJS-AI_orchestration/
./scripts/system-install.sh
./scripts/env-prepare.sh
```

## Project
`scripts/`
Install & configure scripts for the system

`flyte-projects/`
Examples of full MLOps pipelines

`conf/`
Yaml files for kubernetes and software running on kubernetes. Single source of truth for ArgoCD

`docs/`
Explanation and procedures for creating and using our system. TBC.

`docker/`
Centralized dockerfiles and building scripts. TBC.
