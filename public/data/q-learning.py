import sys
import random
import numpy as np
np.set_printoptions(threshold=sys.maxsize)
from utils import matrix_from_csv, read_inputs, read_from_csv, export_to_csv

# Initialization of tables and positions
learning_rate, episodes, tries, discount, penalty, epsilon = read_inputs("data/inputs.csv")
initial_pos   = read_from_csv("data/agent.csv")
goal_pos      = read_from_csv("data/goal.csv")
rewards       = matrix_from_csv("data/rewards.csv")
q_table       = matrix_from_csv("results/qtable-python.csv")
agent_pos     = np.copy(initial_pos)

# Comparison parameters
# random.seed(20)               # Use specific seed
generate_rnd_values = False     # Generate and save random generated numbers
best_reward = 0                 # Best reward found through episodes
rnd_values = []                 # If generate_rnd_values is true, holds the generated random numbers

# Check every available option on a specific state
def is_valid_move(direction):
    global agent_pos
    if   direction == 0 and agent_pos[1] > 0 and rewards[agent_pos[0]][agent_pos[1] - 1] != -10:               # Check left
        return True
    elif direction == 1 and agent_pos[1] < len(rewards)-1 and rewards[agent_pos[0]][agent_pos[1] + 1] != -10:  # Check right
        return True
    elif direction == 2 and agent_pos[0] > 0 and rewards[agent_pos[0] - 1][agent_pos[1]] != -10:               # Check up
        return True
    elif direction == 3 and agent_pos[0] < len(rewards)-1 and rewards[agent_pos[0] + 1][agent_pos[1]] != -10:  # Check down
        return True
    else:
        return False

# Move agent to new state and return a reward for this action
def make_move(direction):
    global agent_pos

    if   direction == 0 and is_valid_move(0):       # Move Left
        agent_pos[1] -= 1
    elif direction == 1 and is_valid_move(1):       # Move Right
        agent_pos[1] += 1
    elif direction == 2 and is_valid_move(2):       # Move Up
        agent_pos[0] -= 1
    elif direction == 3 and is_valid_move(3):       # Move Down
        agent_pos[0] += 1
    else:
        return tuple(q_table[agent_pos[0]][agent_pos[1]]), penalty

    return tuple(q_table[agent_pos[0]][agent_pos[1]]), rewards[agent_pos[0]][agent_pos[1]]

# Q-learning algorithm
for i in range(0, episodes):         
    max_reward = 0

    # Loop through availiable tries
    for j in range(0, tries):
        current_state = tuple(np.copy(agent_pos))

        uniform = random.uniform(0, 1)

        # If random number is less than ε then explore else exploit (make agent greedy)
        if uniform < epsilon:
            action = random.randint(0, 3)
            if generate_rnd_values:
                rnd_values.append([i, j, uniform, action])
        else:
            action = np.argmax(q_table[agent_pos[0]][agent_pos[1]])

        new_state, reward = make_move(action)
        max_reward += reward
        max_future_q = np.max(new_state)
        current_q = q_table[current_state[0]][current_state[1]][action]
        new_q = current_q + learning_rate * (reward + discount * max_future_q - current_q)
        q_table[current_state[0]][current_state[1]][action] = new_q
                    
        if reward == rewards[goal_pos[0]][goal_pos[1]]:
            break

        current_state = new_state

    # Update best reward found from all iterations
    if i == 0 or best_reward < max_reward:
        best_reward = max_reward

    # Reset agent's position to initial position
    agent_pos = np.copy(initial_pos)
    
    # Reduce the greedy parameter
    if epsilon > 0.01:
        epsilon *= 97/100

# Export learned policy to csv
export_to_csv("federated_data/policies/qtable.csv", q_table)

# Ecport best reward found
with open("federated_data/rewards/best_reward.csv", "w") as f:
    f.write(str(best_reward))

if generate_rnd_values:
    export_to_csv("results/rnd_values.csv", rnd_values)
