#!/bin/bash

kubectl delete ns -A --all
sudo microk8s reset
sudo snap remove microk8s --purge
conda env remove --name ray
