#!/usr/bin/env python

"""
Adapted from: https://github.com/ray-project/ray/blob/master/rllib/examples/envs/external_envs/cartpole_server.py


Example of running an RLlib policy server, allowing connections from
external environment running clients. The server listens on
(a Highway env
in this case) against an RLlib policy server listening on one or more
HTTP-speaking ports. See `highway_client.py` in this same directory for how
to start any number of clients (after this server has been started).

This script will not create any actual env to illustrate that RLlib can
run w/o needing an internalized environment.

Setup:
1) Start this server:
    $ python highway_server.py --num-workers --[other options]
      Use --help for help.

2) Run n policy clients:
    See `highway_client.py` on how to do this.

# Note that for NAOMI usecase num of workers have to be equal to number of Ray workers!
# Port for all workers are the same as each rollout worker will live in a separate container (Ray worker)
# This applies both if you are running on multiple RPI or on a single VM with multiple Ray workers

The `num-workers` setting will allow you to distribute the incoming feed over n
listen sockets (in original example, between 9900 and 990n with n=worker_idx-1).
You may connect more than one policy client to any open listen port.
"""

import argparse
import gymnasium as gym
import os
import numpy

import ray
from ray import air, tune
from ray.air.constants import TRAINING_ITERATION
from ray.rllib.env.policy_server_input import PolicyServerInput
from ray.rllib.examples.metrics.custom_metrics_and_callbacks import MyCallbacks
from ray.rllib.utils.metrics import (
    ENV_RUNNER_RESULTS,
    EPISODE_RETURN_MEAN,
    NUM_ENV_STEPS_SAMPLED_LIFETIME,
)

from ray.tune.logger import pretty_print
from ray.tune.registry import get_trainable_cls

import s3fs
import pyarrow.fs
from ray.rllib.policy.policy import PolicySpec

VM_IP="<CHANGE_ME>"

s3_fs = s3fs.S3FileSystem(
    key='minio',
    secret='miniostorage',
    endpoint_url=f'http://{VM_IP}:30085',
    use_ssl="False"
)
custom_fs = pyarrow.fs.PyFileSystem(pyarrow.fs.FSSpecHandler(s3_fs))

SERVER_ADDRESS = "0.0.0.0"
# In this example, the user can run the policy server with
# n workers, opening up listen ports 9900 - 990n (n = num_env_runners - 1)
# to each of which different clients may connect.
SERVER_BASE_PORT = 9900  # + worker-idx - 1

CHECKPOINT_FILE = "last_checkpoint_{}.out"


def get_cli_args():
    """Create CLI parser and return parsed arguments"""
    parser = argparse.ArgumentParser()

    # Example-specific args.
    parser.add_argument(
        "--port",
        type=int,
        default=SERVER_BASE_PORT,
        help="The base-port to use (on localhost). " f"Default is {SERVER_BASE_PORT}.",
    )
    parser.add_argument(
        "--callbacks-verbose",
        action="store_true",
        help="Activates info-messages for different events on "
        "server/client (episode steps, postprocessing, etc..).",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=3, # == num of Ray workers
        help="The number of workers to use. Each worker will create "
        "its own listening socket for incoming experiences. For NAOMI this number should equal to the number of Ray workers!",
    )
    parser.add_argument(
        "--no-restore",
        action="store_true",
        help="Do not restore from a previously saved checkpoint (location of "
        "which is saved in `last_checkpoint_[algo-name].out`).",
    )

    # General args.
    parser.add_argument(
        "--run",
        default="PPO",
        choices=["APEX", "DQN", "IMPALA", "PPO", "R2D2"],
        help="The RLlib-registered algorithm to use.",
    )
    parser.add_argument("--num-cpus", type=int, default=3)
    parser.add_argument(
        "--framework",
        choices=["tf", "tf2", "torch"],
        default="torch",
        help="The DL framework specifier.",
    )
    parser.add_argument(
        "--use-lstm",
        action="store_true",
        help="Whether to auto-wrap the model with an LSTM. Only valid option for "
        "--run=[IMPALA|PPO|R2D2]",
    )
    parser.add_argument(
        "--stop-iters", type=int, default=200, help="Number of iterations to train."
    )
    parser.add_argument(
        "--stop-timesteps",
        type=int,
        default=500000,
        help="Number of timesteps to train.",
    )
    parser.add_argument(
        "--stop-reward",
        type=float,
        default=80.0,
        help="Reward at which we stop training.",
    )
    parser.add_argument(
        "--as-test",
        action="store_true",
        help="Whether this script should be run as a test: --stop-reward must "
        "be achieved within --stop-timesteps AND --stop-iters.",
    )
    parser.add_argument(
        "--no-tune",
        action="store_true",
        help="Run without Tune using a manual train loop instead. Here,"
        "there is no TensorBoard support.",
    )
    parser.add_argument(
        "--local-mode",
        action="store_true",
        help="Init Ray in local mode for easier debugging.",
    )

    args = parser.parse_args()
    print(f"Running with following CLI args: {args}")
    return args


if __name__ == "__main__":
    args = get_cli_args()
    runtime_env = {"pip": ["gym", "highway_env"]}
    ray.init(address=f"ray://{VM_IP}:30001", ignore_reinit_error=True, runtime_env=runtime_env)

    # `InputReader` generator (returns None if no input reader is needed on
    # the respective worker).
    def _input(ioctx):
        # We are remote worker or we are local worker with num_env_runners=0:
        # Create a PolicyServerInput.
        if ioctx.worker_index > 0 or ioctx.worker.num_workers == 0:
            return PolicyServerInput(
                ioctx,
                SERVER_ADDRESS,
                args.port #"+ ioctx.worker_index - (1 if ioctx.worker_index > 0 else 0), # this is not needed for NAOMI as they run in separate containers
            )
        # No InputReader (PolicyServerInput) needed.
        else:
            return None


    # def gen_policy(i):
    #     config = {
    #         "gamma": 0.99,
    #     }
    #     return PolicySpec(config=config)
    #
    #
    # num_agents = 2
    # policies = {f"agent_{i}": gen_policy(i) for i in range(num_agents)}
    # policy_ids = list(policies.keys())
    #
    #
    # def policy_mapping_fn(agent_id, episode, worker, **kwargs):
    #     pol_id = agent_id
    #     return pol_id


    # Algorithm config. Note that this config is sent to the client only in case
    # the client needs to create its own policy copy for local inference.
    config = (
        get_trainable_cls(args.run).get_default_config()
        # Indicate that the Algorithm we setup here doesn't need an actual env.
        # Allow spaces to be determined by user (see below).
        .environment(
            env=None,
            observation_space=gym.spaces.Box(float("-inf"), float("inf"), (5,5)), # copy this from the env you are using
            action_space=gym.spaces.Discrete(5), #
        )
        # DL framework to use.
        .framework(args.framework)
        # Create a "chatty" client/server or not.
        .callbacks(MyCallbacks if args.callbacks_verbose else None)
        # Use the `PolicyServerInput` to generate experiences.
        .offline_data(input_=_input)
        # Use n worker processes to listen on different ports.
        .env_runners(
            num_env_runners=args.num_workers,
            # Connectors are not compatible with the external env.
            enable_connectors=False,
            # this ensures that rollout workers are distributed evenly across workers:
            custom_resources_per_env_runner={"vm": 1} # change this to rasp if you have RPIs in a cluster,
            # num_cpus_per_env_runner

        )
        # this doesnt work yet
        # .multi_agent(
        #     policies=policies,
        #     policy_mapping_fn=policy_mapping_fn
        # )
        # Disable OPE, since the rollouts are coming from online clients.
        .evaluation(off_policy_estimation_methods={})
        # Set to INFO so we'll see the server's actual address:port.
        .debugging(log_level="DEBUG")
    )
    # Disable RLModules because they need connectors
    # config.api_stack(enable_rl_module_and_learner=False)

    # DQN.
    if args.run == "DQN" or args.run == "APEX" or args.run == "R2D2":
        # Example of using DQN (supports off-policy actions).
        config.update_from_dict(
            {
                "num_steps_sampled_before_learning_starts": 100,
                "min_sample_timesteps_per_iteration": 200,
                "n_step": 3,
                "rollout_fragment_length": 4,
                "train_batch_size": 8,
            }
        )
        config.model.update(
            {
                "fcnet_hiddens": [64],
                "fcnet_activation": "linear",
            }
        )
        if args.run == "R2D2":
            config.model["use_lstm"] = args.use_lstm

    elif args.run == "IMPALA":
        config.update_from_dict(
            {
                "num_gpus": 0,
                "model": {"use_lstm": args.use_lstm},
            }
        )

    # PPO.
    else:
        # Example of using PPO (does NOT support off-policy actions).
        config.update_from_dict(
            {
                "rollout_fragment_length": "auto",
                "train_batch_size": 128,
                "model": {"use_lstm": args.use_lstm},
            }
        )

    checkpoint_path = CHECKPOINT_FILE.format(args.run)
    # Attempt to restore from checkpoint, if possible.
    if not args.no_restore and os.path.exists(checkpoint_path):
        checkpoint_path = open(checkpoint_path).read()
    else:
        checkpoint_path = None

    # Manual training loop (no Ray tune).
    if args.no_tune:
        algo = config.build()

        if checkpoint_path:
            print("Restoring from checkpoint path", checkpoint_path)
            algo.restore(checkpoint_path)

        # Serving and training loop.
        ts = 0
        for _ in range(args.stop_iters):
            results = algo.train()
            print(pretty_print(results))
            checkpoint = algo.save().checkpoint
            print("Last checkpoint", checkpoint)
            with open(checkpoint_path, "w") as f:
                f.write(checkpoint.path)
            if (
                results[ENV_RUNNER_RESULTS][EPISODE_RETURN_MEAN] >= args.stop_reward
                or ts >= args.stop_timesteps
            ):
                break
            ts += results[f"{NUM_ENV_STEPS_SAMPLED_LIFETIME}"]

        algo.stop()

    # Run with Tune for auto env and algo creation and TensorBoard.
    else:
        print("Ignoring restore even if previous checkpoint is provided...")

        stop = {
            TRAINING_ITERATION: args.stop_iters,
            NUM_ENV_STEPS_SAMPLED_LIFETIME: args.stop_timesteps,
            f"{ENV_RUNNER_RESULTS}/{EPISODE_RETURN_MEAN}": args.stop_reward,
        }

        tune.Tuner(
            args.run, param_space=config,
            run_config=air.RunConfig(stop=stop, verbose=2, storage_path="raybuck/rllib", storage_filesystem=custom_fs),
        ).fit()
