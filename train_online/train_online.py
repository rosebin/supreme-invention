'''
https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html
'''
import random
import sys
from collections import namedtuple
from itertools import count
from tqdm import tqdm

import matplotlib.pyplot as plt
import numpy as np
import torch

sys.path.append(".")

from Agent.ActorCriticAgent import ActorCriticAgent
from Agent.HandAgent import HandAgent
from ICRAField import ICRAField
from SupportAlgorithm.NaiveMove import NaiveMove

move = NaiveMove()

TARGET_UPDATE = 100

seed = 233
torch.random.manual_seed(seed)
torch.cuda.random.manual_seed(seed)
np.random.seed(seed)
random.seed(seed)

env = ICRAField()
agent = ActorCriticAgent()
agent.load_model()
agent2 = HandAgent()
episode_durations = []

num_episodes = 1001
losses = []
rewards = []
for i_episode in range(1, num_episodes):
    print("Epoch: [{}/{}]".format(i_episode, num_episodes))
    # Initialize the environment and state
    action = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    pos = env.reset()
    agent2.reset(pos)
    state, reward, done, info = env.step(action)
    for t in tqdm(range(2*60*30)):
        # Other agent
        env.setRobotAction("robot_1", agent2.select_action(
            env.getStateArray("robot_1")))
        # Select and perform an action
        state = env.state_dict["robot_0"]["detect"]
        state_map = agent.perprocess_state(state)
        a = agent.select_action(state_map, "sample")
        action = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        if a == 0:
            action[0] = +1.0
        elif a == 1:
            action[0] = -1.0
        elif a == 2:
            action[1] = +1.0
        elif a == 3:
            action[1] = -1.0
        elif a == 4:
            action[2] = +1.0
        elif a == 5:
            action[2] = -1.0
        if env.state_dict["robot_0"]["robot_1"][0] > 0:
            action[4] = +1.0
        else:
            action[4] = 0.0

        # Step
        next_state, reward, done, info = env.step(action)
        next_state = env.state_dict["robot_0"]["detect"]
        next_state_map = agent.perprocess_state(next_state)

        # Store the transition in memory
        agent.push(state, next_state, [a], [reward])
        state = next_state
        state_map = next_state_map

        # Perform one step of the optimization (on the target network)
        if done:
            break

    print("Simulation end in: {}:{:02d}, reward: {}".format(t//(60*30), t % (60*30)//30, env.reward))
    agent.memory.finish_epoch()
    loss = agent.optimize_offline(1)
    #loss = agent.test_model()
    #print("Test loss: {}".format(loss))
    losses.append(loss)
    rewards.append(env.reward)
    episode_durations.append(t + 1)

    # Update the target network, copying all weights and biases in DQN
    if i_episode % TARGET_UPDATE == 0:
        #agent.update_target_net()
        agent.save_model()

print('Complete')
plt.plot(losses)
plt.savefig("loss.pdf")
plt.figure()
plt.title("Reward")
plt.xlabel("Epoch")
plt.ylabel("Final reward")
plt.plot(rewards)
plt.savefig("reward.pdf")
env.close()