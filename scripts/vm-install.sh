#!/bin/bash
# Install sript for kubernetes on on-premise VM. NOT TESTED!

set -e
trap 'echo "Install script for VM was not successful!"; exit 1' ERR

VM_IP=localhost

# Install microk8s
sudo apt update && sudo apt upgrade -y && sudo apt install snapd -y
sudo snap install microk8s --classic --channel=1.27/stable
sleep 10

sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube
newgrp microk8s

export PATH=$PATH:/snap/bin
sleep 10

# Enable addons
microk8s status --wait-ready
microk8s enable dns
microk8s enable ingress
microk8s enable storage
microk8s enable dashboard
microk8s status --wait-ready

# Alias microk8s kubectl to kubectl
sudo snap alias microk8s.kubectl kubectl
sleep 20

# Install ArgoCD on kubernetes + apply our system's source of truth
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
kubectl config set-context --current --namespace=argocd
kubectl apply -f ../conf/kube_conf/argocd/apps.yaml

# Download and install the ArgoCD CLI
echo "Downloading and installing ArgoCD CLI..."
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64

microk8s config > $HOME/.kube/config

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

echo "Go to VM_IP:$(echo $ARGOCD_PORT) for ArgoCD console!"

# TODO before apps will deploy correctly repo needs to be public or github keys need to be setup
