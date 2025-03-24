#!/bin/bash

# Install k3s if not already installed version v1.31.3+k3s1
if ! command -v k3s &> /dev/null
then
  echo "k3s not found. Installing k3s..."
  curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.31.3+k3s1 sh -
  sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
fi

# check if helm and kubectl are working, if not alert user and exit
if ! command -v helm &> /dev/null || ! command -v kubectl &> /dev/null
then
  echo "Helm or kubectl not found. Please install and try again."
  exit
fi

# Disable default Traefik; install Nginx for compatibility with microk8s
kubectl delete -n kube-system helmcharts.helm.cattle.io traefik
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# custom StorageClass in k3s with name microk8s-hostpath for compatibility with microk8s
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: microk8s-hostpath
provisioner: rancher.io/local-path
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
EOF

echo "NAOMI can now be installed on k3s."
