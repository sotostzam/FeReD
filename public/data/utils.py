import sys
import csv
import numpy as np
import random
import os
                    
# Export matrix to csv
def export_to_csv(location, matrix):
    with open(location, "w") as f:
        writer = csv.writer(f, delimiter=";")
        if len(np.shape(matrix)) == 1:
            writer.writerow(matrix)
        else:
            for i in range(len(matrix)):
                if len(matrix[i]) == 4:
                    writer.writerow(matrix[i])
                else:
                    for j in range(len(matrix[i])):
                        if len(np.shape(matrix)) == 3:
                            for k in range(len(matrix[i][j])):
                                writer.writerow([i, j, k, matrix[i][j][k]])
                        else:
                            writer.writerow([i, j, matrix[i][j]])

# Reconstruct Q-table from csv  
def matrix_from_csv(file_loc):
    with open(file_loc) as f:
        vals = list(csv.reader(f, delimiter=";"))
        if len(vals[0]) == 3:
            size = int(np.sqrt(len(vals)))
            matrix = np.zeros((size,size))
            for val in vals:
                matrix[int(val[0]), int(val[1])] = float(val[2])
        else:
            size = int(np.sqrt(len(vals)/4))
            matrix = np.zeros((size,size,4))
            for val in vals:
                matrix[int(val[0]), int(val[1]), int(val[2])] = float(val[3])
        return matrix
    
# Import inputs from csv file    
def read_inputs(file_loc):
    with open(file_loc) as f:
        vals = list(csv.reader(f, delimiter=";"))[0]
        return [float(vals[0]), int(vals[1]), int(vals[2]), float(vals[3]), int(vals[4]), float(vals[5])]
        
# Import agent position from csv file     
def read_from_csv(file_loc):
    filesize = os.path.getsize(file_loc)
    if filesize == 0:
        return False
    with open(file_loc) as f:
        vals = list(csv.reader(f, delimiter=";"))[0]
        if len(vals) == 3:
            return [int(vals[0]), int(vals[1]), int(vals[2])]
        return [int(vals[0]), int(vals[1])]

# Update input values
def update_inputs(**kargs):
    inputs = read_inputs("data/inputs.csv")
    for key, value in kargs.items():
        if key == "episodes":
            inputs[1] = value
        if key == "tries":
            inputs[2] = value
        if key == "epsilon":
            inputs[-1] = value
    export_to_csv("data/inputs.csv", inputs)
    
# Randomize initial position
def randomize_init_pos(return_found=False):
    rewards = matrix_from_csv("data/rewards.csv")
    size = rewards.shape[0]
    found = False
    pos = []
    while not found:
        temp = [random.randint(0,size-1), random.randint(0,size-1)]
        if rewards[temp[0]][temp[1]] != -10 and rewards[temp[0]][temp[1]] !=100:
            found = True
            pos = temp
    export_to_csv("data/agent.csv", [pos[0], pos[1], pos[0], pos[1]])

    if return_found:
        return pos
    
# Prepare the input files before running the implementations
def prepare(partition="horizontal"):
    EPISODES      = int(sys.argv[1])
    TRIES         = int(sys.argv[2])
    SIZE          = str(sys.argv[3])
    LEARNING_RATE = float(sys.argv[4])
    EPSILON       = float(sys.argv[5])
    DISCOUNT      = 0.95
    PENALTY       = -10

    maze_file   = np.genfromtxt(('datasets/custom-maze_'+SIZE+'.csv'), delimiter=',', dtype = int)
    initial_pos = np.array([0, 0])
    goal_pos    = np.array([0, 0])
    rewards     = np.ones((maze_file.shape[0], maze_file.shape[1])) * - 1
    q_table     = np.zeros((len(rewards), len(rewards), 4))
    for i in range (0, maze_file.shape[0]):
        for j in range (0, maze_file.shape[1]):
            if maze_file[i, j] == 1:
                rewards[i, j] = -10
            elif maze_file[i, j] == 2:
                initial_pos = [i, j]
                agent_pos = np.copy(initial_pos)
            elif maze_file[i, j] == 3:
                goal_pos = [i, j]
                rewards[goal_pos[0], goal_pos[1]] = 100
            else:
                pass

    # Export parameters to csv files
    export_to_csv("data/inputs.csv", [LEARNING_RATE, EPISODES, TRIES, DISCOUNT, PENALTY, EPSILON])
    if partition == "horizontal":
        export_to_csv("data/agent.csv", [initial_pos[0], initial_pos[1], initial_pos[0], initial_pos[1]])
        export_to_csv("data/goal.csv", [goal_pos[0], goal_pos[1]])
        export_to_csv("data/rewards.csv", rewards)
        export_to_csv("data/qtable.csv", q_table)   
    elif partition == "vertical":
        export_to_csv("data/global-agent.csv", [initial_pos[0], initial_pos[1], initial_pos[0], initial_pos[1]])
        export_to_csv("data/global-goal.csv", [goal_pos[0], goal_pos[1]])
        export_to_csv("data/global-rewards.csv", rewards)
        export_to_csv("data/global-qtable.csv", q_table)

def find_next_candidate(format):
    qtable = matrix_from_csv("data/global-qtable-" + format + ".csv")
    rewards = matrix_from_csv("data/global-rewards.csv")
    global_goal = read_from_csv("data/global-goal.csv")
    previous_candidate = read_from_csv("data/candidate-" + format + ".csv")
    explored_states = []

    # Load explored states
    with open("data/explored-states-" + format + ".csv") as f:
        vals = list(csv.reader(f, delimiter=";"))
        for val in vals:
            explored_states.append([int(val[0]), int(val[1])])

    # Add previous candidate to explored states
    if previous_candidate and previous_candidate not in explored_states:
        explored_states.append(previous_candidate)
        with open("data/explored-states-" + format + ".csv", "a") as f:
            f.write(str(previous_candidate[0]) + ";" + str(previous_candidate[1]) + "\n")
            print("Added candidate", previous_candidate, "to explored states")
        
    # Find next candidate state
    candidate = None
    if not explored_states:
        candidate = global_goal
    else:
        best_val = -np.inf
        for i in range(qtable.shape[0]):
            for j in range(qtable.shape[1]):
                if [i,j] not in explored_states:
                    for k in range(qtable.shape[2]):
                        if qtable[i,j,k] > best_val and rewards[i,j] != -10:
                            candidate = [i,j]
                            best_val = qtable[i,j,k]
    
    with open("data/candidate-" + format + ".csv", "w") as f:
        f.write(str(candidate[0]) + ";" + str(candidate[1]))

    update_inputs(epsilon_exact=0.8)

def extract_partition(size, format):
    # Load global parameters into memory
    qtable = matrix_from_csv("data/global-qtable-" + format + ".csv")
    rewards = matrix_from_csv("data/global-rewards.csv")
    global_goal = read_from_csv("data/global-goal.csv")
    candidate = None
    with open("data/candidate-" + format + ".csv") as f:
            val = list(csv.reader(f, delimiter=";"))
            candidate = [int(val[0][0]), int(val[0][1])]

    # Find box containing candidate
    box_radius = [None, None, None, None]
    if candidate[0] - size >= 0:
        box_radius[0] = candidate[0] - size + 1
    else:
        box_radius[0] = 0
    if candidate[0] + size < qtable.shape[0]:
        box_radius[1] = candidate[0] + size
    else:
        box_radius[1] = qtable.shape[0]
    if candidate[1] - size >= 0:
        box_radius[2] = candidate[1] - size + 1
    else:
        box_radius[2] = 0
    if candidate[1] + size < qtable.shape[1]:
        box_radius[3] = candidate[1] + size
    else:
        box_radius[3] = qtable.shape[1]

    # Create random partition
    partition = [random.randint(box_radius[0], box_radius[1]-size), random.randint(box_radius[2], box_radius[3]-size)]
    qtable_partition = qtable[partition[0]:partition[0] + size, partition[1]:partition[1] + size]
    if candidate != global_goal:
        rewards[global_goal[0], global_goal[1]] = -1
    rewards_partition = rewards[partition[0]:partition[0] + size, partition[1]:partition[1] + size]
    local_goal = [candidate[0] - partition[0], candidate[1] - partition[1]]
    rewards_partition[local_goal[0], local_goal[1]] = 100

    export_to_csv("results/qtable-" + format + ".csv", qtable_partition)
    export_to_csv("data/rewards.csv", rewards_partition)
    export_to_csv("federated_data/partitions/partition.csv", [partition[0], partition[1], size])
    export_to_csv("data/goal.csv", local_goal)
    export_to_csv("data/candidate-" + format + ".csv", candidate)
    initial_pos = randomize_init_pos(return_found=True)

    # Create maze layout file (used for snapshots)
    with open('federated_data/layouts/layout.csv', "w") as f:
        for i in range(rewards_partition.shape[0]):
            for j in range(rewards_partition.shape[1]):
                if i == candidate[0] - partition[0] and j == candidate[1] - partition[1]:
                    f.write(str(3))
                elif i == initial_pos[0] and j == initial_pos[1]:
                    f.write(str(2))
                elif rewards_partition[i, j] == -10:
                    f.write(str(1))
                elif rewards_partition[i, j] == -1:
                    f.write(str(0))

                if j != rewards_partition.shape[1] - 1:
                    f.write(", ")
                else:
                    f.write("\n")

def write_times(*args, end_of_round=False):
    with open('results/times.txt', 'a') as f:
        for item in args:
            if item == args[-1] and end_of_round == True:
                f.write(str(item) + "\n")
            else:
                f.write(str(item) + "\t")
