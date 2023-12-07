#!/bin/bash
# this script was not tested!

echo "Please first install microk8s, connect nodes in cluster and enable dns, registry, helm on cluster"
read -rp "Proceed ? [y/n]" answer

if [ "$answer" != "${answer#[Yy]}" ] ;then
    echo "proceding..."
else
    echo "exiting..."
    exit 1
fi

# do all of this on master node
microk8s helm repo add kuberay https://ray-project.github.io/kuberay-helm/ || exit 1
microk8s helm repo update &&

microk8s helm install kuberay-operator kuberay/kuberay-operator --version 1.0.0-rc.0 --namespace ray-system --create-namespace || exit 1
sleep 20
microk8s kubectl get pods
read  -n 1 -p "Input something to proceed:" null

# Deploy a sample RayCluster CR from the KubeRay Helm chart repo, here you can apply custom cr or ray serve
# microk8s helm install raycluster kuberay/ray-cluster --version 1.0.0-rc.0 || exit 1
microk8s kubectl apply -n ray-system -f ../Ray-conf/ray-serve.yaml || exit 1
sleep 20
microk8s kubectl get -n ray-system rayservices
read  -n 1 -p "Input something to proceed:" null
microk8s kubectl get pods -n ray-system
sleep 10

#submiting a job
microk8s kubectl get service -n ray-system || exit 1
microk8s kubectl port-forward --address 0.0.0.0 service/ray-serve-head-svc 8265 10001 &
microk8s kubectl port-forward --address 0.0.0.0 service/ray-serve-serve-svc 8000 &
ray job submit --address http://localhost:8265 -- python -c "import ray; ray.init(); print(ray.cluster_resources())"
