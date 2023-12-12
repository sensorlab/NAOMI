#!/bin/bash

# install miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda3
rm ~/miniconda.sh

# initialize conda
conda init bash
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"

# install pip and requirements
conda install -y pip
pip install -r ../requirements.txt

# TODO
# zenml connect
# zenml connect --url=<replace this part with subshell hostname to get ip from machine> --username=default --password zenml
# zenml set stack from conf/zenml_stack.yaml but adjust the ip of minio
