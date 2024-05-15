#!/bin/bash
# Install sript for kubernetes on on-premise VM. NOT TESTED!

set -e
trap 'echo "System deployment script failed"; exit 1' ERR

VM_IP=localhost

# Enable addons
microk8s status --wait-ready
microk8s enable dns
microk8s enable ingress
microk8s enable storage
microk8s enable dashboard
microk8s status --wait-ready

# Alias microk8s kubectl to kubectl, if kubectl not installed
# sudo snap alias microk8s.kubectl kubectl
microk8s config > $HOME/.kube/config
export KUBECONFIG=/home/bbertalanic/.kube/config
echo "Waiting for system pods.."
kubectl wait --for=condition=ready pod -n kube-system --all --timeout=500s
echo "Done"

# Install ArgoCD on kubernetes + apply our system's source of truth
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
kubectl config set-context --current --namespace=argocd
kubectl apply -f conf/kube_conf/argocd/apps.yaml || { echo "Config file not found. Did you run the script from the root of the repository?"; exit 1; }

# Download and install the ArgoCD CLI
echo "Downloading and installing ArgoCD CLI..."
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64

microk8s config > $HOME/.kube/config

echo "Waiting for argocd pods to start.."
kubectl wait --for=condition=ready pod -n argocd --all --timeout=300s
echo "Done"

# Retrieve the initial password
echo "Retrieving the initial password for the 'admin' account..."
INITIAL_PASSWORD=$(kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d)
echo "Initial password: $INITIAL_PASSWORD"

# Log in to ArgoCD
echo "Logging in to ArgoCD..."
ARGOCD_PORT=$(kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')
argocd login $VM_IP:$ARGOCD_PORT --username admin --password $INITIAL_PASSWORD --insecure

# Prompt the user to update the account password
echo "Please enter a new password for the 'admin' account:"
read -s NEW_PASSWORD
argocd account update-password --current-password $INITIAL_PASSWORD --new-password $NEW_PASSWORD

echo "Go to $(echo $VM_IP):$(echo $ARGOCD_PORT) for ArgoCD console!"

kubectl create ns ray-system
# fix for hardcoded grafana ip
kubectl create configmap grafana-ip --from-literal=GRAFANA_IP="http://$(hostname -i):30000" -n ray-system

# TODO Note that this is hardcoded, some automatic syncing is needed!
echo "Syncing apps:"
argocd app sync minio kuberay-operator ray flyte-binary flyte-resources mlflow prometheus prometheus-grafana-configs --retry-limit 30

echo "Waiting for ray pods to start.."
kubectl wait --for=condition=ready pod -A --all --timeout=800s
echo "Done"
