#!/bin/bash

# Check if conda is installed
if ! which conda > /dev/null; then
    # install miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
    bash ~/miniconda.sh -b -p $HOME/miniconda3
    rm ~/miniconda.sh

    # initialize conda
    conda init bash
    eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
fi

# Check if the 'ray' environment exists
if ! conda env list | grep -q '^ray '; then
    # Create the 'ray' environment
    conda create -n ray python=3.10 -y
fi

# Activate the 'ray' environment
source /$HOME/miniconda3/bin/activate ray

# install pip and requirements
conda install -y pip
pip install -r requirements.txt  || { echo "requirements file not found. Did you run the script from the root of the repository?"; exit 1; }
curl -sL https://ctl.flyte.org/install | sudo bash -s -- -b /usr/local/bin

# Ask the user if Kubernetes is running on the same machine
read -p "Is Kubernetes cluster with zenml running on this machine (y/n)? " answer

case ${answer:0:1} in
    y|Y )
        # If yes, get the IP of VM
        IP=$(hostname -I | awk '{print $1}')
    ;;
    * )
        # If no, ask the user to input the IP of the machine running Kubernetes
        read -p "Please enter the IP of the machine running Kubernetes: " IP
    ;;
esac
# Connect to zenml running on kubernetes
zenml connect --url=http://$IP --username=default --password=zenml

# apply zenml stack from config file, but change the <IP> placeholder to the value of ip
cp conf/zenml_stack.yaml temp.yaml
sed -i "s/<IP>/$IP/g" temp.yaml
zenml stack import temp.yaml
zenml stack set kube_stack

rm temp.yaml # cleanup
export PATH=$PATH:$HOME/miniconda3/bin
echo "Run to start using env:"
echo "conda init bash"
echo "source ~./bashrc"
echo "conda activate ray"
