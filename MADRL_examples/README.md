# Examples of Multi Agent Deep Reinforcement Learning; enabled by NAOMI

## Important

- Multi agent server/client example is not supported by NAOMI 0.1.0 please use source code to install the helm charts after modifying the values file:
```bash
cd helm_charts/NAOMI
helm install naom . -f values_madrl_example.yaml
```
- Use values_madrl_example.yaml to install the helm charts with values for MADRL examples.
- Install requirements.txt (same as NAOMI + gym and highway-env packages.


## Examples
These examples are in development and may require some tweaking of the configs to run.

Change the VM_IP variable in the examples to the IP of the VM where NAOMI is deployed.

### Multi agent highway environment with RLlib. Env is stepped by RLlib.

- `multi_agent_highway.py`

### External highway environment with RLlib, Client - Server configuration. Environment requests actions from RLlib server.

- `highway_client.py`
- `highway_client.py`

Multi agent highway is not yet supported using external RLlib environment.


## Infrastructure configuration
Examples can be run on a single machine using multiple Ray workers or on multiple machines connected with k8s.
In our config we utilize 1VM and 2 Raspberry Pi 5s. Ray workers are deployed on each RPI and on VM.
Reinforcement learning examples are configured to run environment on RPI and Training of algorithms on VM.
This can be modified in the examples depending on your infrastructure.

This presents a use case of agents running on edge devices or on board units and training happening on a central server or roadside units.
A use case of autonomous driving where agents are vehicles and training is done on a roadside units. When algorithm is trained on new observations the new reinforcement learning policies are sent to the agents.

## Results of RL training using Tensorboard

This works if RL is run with examples using RLlib and Ray Tune.

```bash
export AWS_ACCESS_KEY_ID=minio
export AWS_SECRET_ACCESS_KEY=miniostorage
export S3_ENDPOINT=http://<CHANGE_ME_TO_NAOMI_IP>:30085
export S3_VERIFY_SSL=0
export S3_USE_HTTPS=0
tensorboard --logdir=s3://raybuck/rllib/ --host=0.0.0.0
```