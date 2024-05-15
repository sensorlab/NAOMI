#!/bin/bash

kubectl delete ns -A --all
sudo microk8s reset
sudo snap remove microk8s --purge
sudo rm -rf /usr/local/bin/argocd
conda env remove --name ray
