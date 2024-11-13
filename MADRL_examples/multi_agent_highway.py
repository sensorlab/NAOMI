from typing import Tuple
import gymnasium as gym
import highway_env
from ray import tune, air
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.policy.policy import PolicySpec
import ray
import s3fs
import pyarrow.fs
from ray.rllib.env.multi_agent_env import MultiAgentEnv
from ray.rllib.utils.typing import MultiAgentDict

VM_IP = "<CHANGE_ME>"

# Use minio as a filesystem for Ray Tune logs:
# Minio is deployed as part of NAOMI, change the endpoint_url to NAOMI minio endpoint
s3_fs = s3fs.S3FileSystem(
    key='minio',
    secret='miniostorage',
    endpoint_url=f'http://{VM_IP}:30085',
    use_ssl="False"
)
custom_fs = pyarrow.fs.PyFileSystem(pyarrow.fs.FSSpecHandler(s3_fs))

class MultiAgentHighwayEnv(MultiAgentEnv):
    def __init__(self, env_config: dict):
        super().__init__()

        import highway_env
        import gymnasium as gym

        self.env = gym.make('highway-fast-v0', config={
            "controlled_vehicles": env_config["num_vehicles"]})
        self.observation_space = self.env.observation_space
        self.action_space = self.env.action_space

        self.env.unwrapped.config.update({
            "controlled_vehicles": env_config["num_vehicles"],  # Two controlled vehicles
            "observation": {
                "type": "MultiAgentObservation",
                "observation_config": {
                    "type": "Kinematics",
                }
            },
            "action": {
                "type": "MultiAgentAction",
                "action_config": {
                    "type": "DiscreteMetaAction",
                }
            }
        })
        obs, infos = self.env.reset()
        # print(obs)

    def reset(self, seed=None, options=None) -> Tuple[MultiAgentDict, MultiAgentDict]:
        # multi agent should return a dictionary of observations
        obs, infos = self.env.reset()

        # Ensure the obs and infos are dicts where each agent has its observation and info
        obs_dict = {f"agent_{i}": obs[i] for i in range(len(obs))}

        return obs_dict, infos

    def step(self, action: MultiAgentDict) -> Tuple[MultiAgentDict, MultiAgentDict, MultiAgentDict, MultiAgentDict, MultiAgentDict]:

        # multi-agent should accept a dictionary of actions

        actions = tuple(action[f"agent_{i}"] for i in range(len(action)))   # Convert each action to a tuple

        # Step the environment with the list of actions
        obs, rewards, dones, truncated, infos = self.env.step(actions)

        terminateds = {f"agent_{i}": dones for i in range(len(obs))}
        terminateds["__all__"] = dones

        truncated_new = {f"agent_{i}": truncated for i in range(len(obs))}
        truncated_new["__all__"] = truncated

        output = ({f"agent_{i}": obs[i].tolist() for i in range(len(obs))},
            {f"agent_{i}": rewards for i in range(len(obs))},
            terminateds,
            truncated_new,
            {f"agent_{i}": infos for i in range(len(obs))})

        return output

    def render(self) -> None:
        self.env.render()


runtime_env = {"pip": ["gym", "highway_env"]} # TO-DO add these dependencies to Ray docker image
ray.init(address=f"ray://{VM_IP}:30001", ignore_reinit_error=True, runtime_env=runtime_env)

# Define the multi-agent policies
def gen_policy(i):
    config = {
        "gamma": 0.99,
    }
    return PolicySpec(config=config)


num_agents = 2
policies = {f"agent_{i}": gen_policy(i) for i in range(num_agents)}
policy_ids = list(policies.keys())


def policy_mapping_fn(agent_id, episode, worker, **kwargs):
    pol_id = agent_id
    return pol_id


# Use the new PPOConfig API
config = (
    PPOConfig()
    .environment(MultiAgentHighwayEnv, env_config={"num_vehicles": num_agents})
    .framework("torch")
    .multi_agent(
        policies=policies,
        policy_mapping_fn=policy_mapping_fn
    )
    .rollouts(
        num_rollout_workers=2,
        rollout_fragment_length="auto",
        sample_timeout_s=1200
    )
    .training(
        num_sgd_iter=10,
        train_batch_size=512,
        sgd_minibatch_size=32,
    )
    # note if you don't have RPIs in your k8s cluster you can skip custom_resources_per_worker
    # custom_resources_per_worker={"rasp": 1}
    .resources(num_gpus=0, num_cpus_for_main_process=2)
    .debugging() # log_level="DEBUG"
)

## uncomment this part for a manual training loop
# algo = config.build()
#
# # Training loop
# for i in range(1):
#     result = algo.train()
#     print(f"Iteration {i}: {result}")


# Training using Ray Tune, with stop conditions:
stop = {
    # "episode_reward_mean": 70,
    #"timesteps_total": 1024 #16384, # 4096*2*2
    "training_iteration": 300,
}

results = tune.Tuner(
    "PPO",
    param_space=config.to_dict(),
    run_config=air.RunConfig(stop=stop, verbose=1, storage_path="raybuck/rllib", storage_filesystem=custom_fs),
).fit()
