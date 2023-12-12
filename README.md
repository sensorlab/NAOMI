# IJS AI orchestration

Our system is managed by ArgoCD, all changes to conf/kube_conf will be picked up by Argo and can be synced manually or automaticaly to our cluster.

To recreate our system:
- Use at least one node with Ubuntu installed (Tested with 22.04.1-Ubuntu)
- Clone the repo
- Run install script `./scripts/vm-install.sh` which installs microk8s and argocd and automatically deploys all our apps on the cluster.
- Run install script `scripts/rasp-install.sh` on any raspberry pi node you want to join to the cluster
- Install requirements.txt on VM + configure zenml to connect to zenml server (script TODO)
- Run zenml pipelines by running run.py in zenml projects.

## Project
`scripts/`
Install & configure scripts for the system

`zenml-projects/`
Examples of full MLOps pipelines

`conf/`
Yaml files for kubernetes and software running on kubernetes. Single source of truth for ArgoCD

`docs/`
Explanation and procedures for creating and using our system. TBC.

`docker/`
Centralized dockerfiles and building scripts. TBC.
