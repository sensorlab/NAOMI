#!/usr/bin/env python

"""
Adapted from: https://github.com/ray-project/ray/blob/master/rllib/examples/envs/external_envs/cartpole_client.py

Example of running an external simulator (a Highway env
in this case) against an RLlib policy server listening on one or more
HTTP-speaking port(s). See `highway_server.py` in this same directory for
how to start this server.

This script will only create one single env altogether to illustrate
that RLlib can run w/o needing an internalized environment.

Setup:
1) Start the policy server:
    See `highway_server.py` on how to do this.
2) Run this client:
    $ python highway_client.py --inference-mode=local|remote --[other options]
      Use --help for help.

# local should be used by default, remote did not work for me

In "local" inference-mode, the action computations are performed
inside the PolicyClient used in this script w/o sending an HTTP request
to the server. This reduces network communication overhead, but requires
the PolicyClient to create its own RolloutWorker (+Policy) based on
the server's config. The PolicyClient will retrieve this config automatically.
You do not need to define the RLlib config dict here!

In "remote" inference mode, the PolicyClient will send action requests to the
server and not compute its own actions locally. The server then performs the
inference forward pass and returns the action to the client.

In either case, the user of PolicyClient must:
- Declare new episodes and finished episodes to the PolicyClient.
- Log rewards to the PolicyClient.
- Call `get_action` to receive an action from the PolicyClient (whether it'd be
  computed locally or remotely).
- Besides `get_action`, the user may let the PolicyClient know about
  off-policy actions having been taken via `log_action`. This can be used in
  combination with `get_action`, but will only work, if the connected server
  runs an off-policy RL algorithm (such as DQN, SAC, or DDPG).
"""

import argparse
import gymnasium as gym
import highway_env
from ray.rllib.env.policy_client import PolicyClient

VM_IP="<CHANGE_ME>"

parser = argparse.ArgumentParser()
parser.add_argument(
    "--no-train", action="store_true", help="Whether to disable training."
)
parser.add_argument(
    "--inference-mode", type=str, default="local", choices=["local", "remote"]
)
parser.add_argument(
    "--off-policy",
    action="store_true",
    help="Whether to compute random actions instead of on-policy "
    "(Policy-computed) ones.",
)
parser.add_argument(
    "--stop-reward",
    type=float,
    default=9999,
    help="Stop once the specified reward is reached.",
)
parser.add_argument(
    "--port", type=int, default=30070, help="The port to use (on localhost)."
)

if __name__ == "__main__":
    args = parser.parse_args()

    # The following line is the only instance, where an actual env will
    # be created in this entire example (including the server side!).
    # This is to demonstrate that RLlib does not require you to create
    # unnecessary env objects within the PolicyClient/Server objects, but
    # that only this following env and the loop below runs the entire
    # training process.
    env = gym.make('highway-fast-v0')

    # Get and print the observation space
    # You can copy this info to highway_server.py to define config
    obs_space = env.observation_space
    act_space = env.action_space
    print("Observation space:", obs_space)
    print("action space:", act_space)

    # In our case by using NodePort all workers are listening on the same port and Loadbalancing is handled by Kuberentes
    # Note that this is different to the original example provided by Ray RLlib
    client = PolicyClient(
        f"http://{VM_IP}:{args.port}", inference_mode=args.inference_mode
    )

    # In the following, we will use our external environment (the Highway env
    # env we created above) in connection with the PolicyClient to query
    # actions (from the server if "remote"; if "local" we'll compute them
    # on this client side), and send back observations and rewards.

    # Start a new episode.
    obs, info = env.reset()
    print(obs)
    eid = client.start_episode(training_enabled=not args.no_train)

    rewards = 0.0
    while True:
        # Compute an action randomly (off-policy) and log it.
        if args.off_policy:
            action = env.action_space.sample()
            client.log_action(eid, obs, action)
        # Compute an action locally or remotely (on server).
        # No need to log it here as the action
        else:
            action = client.get_action(eid, obs)

        # Perform a step in the external simulator (env).
        obs, reward, terminated, truncated, info = env.step(action)
        rewards += reward

        # Log next-obs, rewards, and infos.
        client.log_returns(eid, reward, info=info)
        env.render()
        # Reset the episode if done.
        if terminated or truncated:
            print("Total reward:", rewards)
            if rewards >= args.stop_reward:
                print("Target reward achieved, exiting")
                exit(0)

            rewards = 0.0

            # End the old episode.
            client.end_episode(eid, obs)

            # Start a new episode.
            obs, info = env.reset()
            eid = client.start_episode(training_enabled=not args.no_train)
