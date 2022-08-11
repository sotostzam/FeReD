import sys
import csv
import numpy as np
import random
import os
import math
import subprocess

# Manhattan distance of two points
def man_distance(point1, point2):
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])
    
def euclidean_distance(point1, point2):
    return np.linalg.norm(np.array(point1)-np.array(point2))
    
def dist_similarity(point1, point2):
    return sig_deriv(euclidean_distance(point1, point2))

# Helper function to map one range to another        
def normalize_range(current_min, current_max, target_min, target_max, value):
    if current_min < current_max:
        return ((value - current_min) / (current_max - current_min)) * (target_max - target_min) + target_min
    else:
        return 0

# Derivative of the sigmoid function 
def sig_deriv(z):
    a = 2
    b = 0.3
    sig = a / (1 + np.exp(-b*z))
    return sig * (a - sig)
                    
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
    if partition == "vertical":
        export_to_csv("data/global-agent.csv", [initial_pos[0], initial_pos[1], initial_pos[0], initial_pos[1]])
        export_to_csv("data/global-goal.csv", [goal_pos[0], goal_pos[1]])
        export_to_csv("data/global-rewards.csv", rewards)
        export_to_csv("data/global-qtable.csv", q_table)

# Find the next best candidate state to explore (Vertical Partitioning)
def find_next_candidate(format):        
    qtable          = matrix_from_csv("data/global-qtable-" + format + ".csv")
    rewards         = matrix_from_csv("data/global-rewards.csv")
    global_goal     = read_from_csv("data/global-goal.csv")
    prev_candidate  = read_from_csv("data/candidate-" + format + ".csv")
    explored_states = []

    # Load explored states
    with open("data/explored-states-" + format + ".csv") as f:
        vals = list(csv.reader(f, delimiter=";"))
        for val in vals:
            explored_states.append([int(val[0]), int(val[1])])

    # Add previous candidate to explored states
    if prev_candidate and prev_candidate not in explored_states:
        explored_states.append(prev_candidate)
        with open("data/explored-states-" + format + ".csv", "a") as f:
            f.write(str(prev_candidate[0]) + ";" + str(prev_candidate[1]) + "\n")
        
    # Find next candidate state
    candidate = None
    global_start = read_from_csv("data/global-agent.csv")
    if not explored_states:
        candidate = global_goal
    else:
        candidate_list = []
        for state in explored_states:
            i, j = state
            # Check the four states surrounding current explored state
            if i-1 >= 0 and [i-1, j] not in explored_states and rewards[i-1, j] != -10:
                candidate_list.append([(i-1, j), max(qtable[i-1, j])])
            if i+1 < qtable.shape[0] and [i+1, j] not in explored_states and rewards[i+1, j] != -10:
                candidate_list.append([(i+1, j), max(qtable[i+1, j])])
            if j-1 >= 0 and [i, j-1] not in explored_states and rewards[i, j-1] != -10:
                candidate_list.append([(i, j-1), max(qtable[i, j-1])])
            if j+1 < qtable.shape[1] and [i, j+1] not in explored_states and rewards[i, j+1] != -10:
                candidate_list.append([(i, j+1), max(qtable[i, j+1])])
               
            # Sort candidate list and keep top K candidates
            candidate_list.sort(reverse = True, key = lambda x: x[1])
            while len(candidate_list) > 5:
                candidate_list.pop()
        
        # Start scoring candidates and select best one        
        selected_candidate = None
        if len(candidate_list) == 1:
            selected_candidate = candidate_list[0]
        else:
            best = 0
            val_min = min(candidate_list, key = lambda x: x[1])[1]
            val_max = max(candidate_list, key = lambda x: x[1])[1]
            dis_min = min(candidate_list, key = lambda x: euclidean_distance(x[0], global_start))
            dis_max = max(candidate_list, key = lambda x: euclidean_distance(x[0], global_start))
            dis_worst = sig_deriv(euclidean_distance(dis_max[0], global_start))
            dis_best  = sig_deriv(euclidean_distance(dis_min[0], global_start))
            
            for candidate in candidate_list:
                norm_q_val = normalize_range(val_min, val_max, 0, 0.5, candidate[1])
                norm_dist = normalize_range(dis_worst, dis_best, 0, 0.5, dist_similarity(candidate[0], global_start))
                score = norm_q_val + norm_dist
                
                if score > best:
                    best = score
                    selected_candidate = candidate
                    
            if best == 0:
                selected_candidate = candidate_list[0]
            
        candidate = selected_candidate[0]
    
    with open("data/candidate-" + format + ".csv", "w") as f:
        f.write(str(candidate[0]) + ";" + str(candidate[1]))

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
    global_goal_val = rewards[global_goal[0], global_goal[1]]
    partition = [random.randint(box_radius[0], box_radius[1]-size), random.randint(box_radius[2], box_radius[3]-size)]
    qtable_partition = qtable[partition[0]:partition[0] + size, partition[1]:partition[1] + size]
    if candidate != global_goal:
        rewards[global_goal[0], global_goal[1]] = -1
    rewards_partition = rewards[partition[0]:partition[0] + size, partition[1]:partition[1] + size]
    local_goal = [candidate[0] - partition[0], candidate[1] - partition[1]]
    rewards_partition[local_goal[0], local_goal[1]] = global_goal_val
    qtable_partition[local_goal[0], local_goal[1]] = np.zeros(4)

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

# Compare the results from the implementations
def compare_equality():
    with open('results/qtable-python.csv') as tb1, open('results/qtable-sql.csv') as tb2:
        tb1_rows = list(csv.reader(tb1, delimiter=";"))
        tb2_rows = list(csv.reader(tb2, delimiter=";"))
        equal = True
        index = 0
        while equal is True and index < len(tb1_rows):
            # Ensure that values are the same within 5 decimal digits
            if not math.isclose(float(tb1_rows[index][-1]), float(tb2_rows[index][-1]), rel_tol=0.00001):
                equal = False
            index += 1
        if equal:
            print('Equality test: Success')
        else:
            print('Equality test: Failed')

# Find worse convergence value from clients
def compute_convergence(operation='compute', round=None, end_of_round=False):
    if operation == "compute":
        directory = "federated_data/rewards"
        vals = []
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            with open(f) as ff:
                val = list(csv.reader(ff, delimiter=";"))
                vals.append(float(val[0][0]))
                        
        with open('federated_data/convergence_vals/convergence.txt', 'w') as f:
            f.write(str(vals[0]) + "\n")
    
    if operation == "average":
        directory = "federated_data/convergence_vals"
        vals = []
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            with open(f) as ff:
                val = list(csv.reader(ff, delimiter=";"))
                vals.append(float(val[0][0]))

        average_val = sum(vals) / len(vals)

        with open('results/convergence.txt', 'a') as f:
            if end_of_round:
                f.write(str(average_val) + "\n")
            elif round is not None:
                f.write(str(round) + "\t" + str(average_val) + "\t")
            else:
                f.write(str(average_val) + "\t")
                
def fixed_compute(lang):
    inputs = read_inputs("data/inputs.csv")
    update_inputs(episodes=1, tries=200, epsilon=0)

    if lang == "python":
        process = subprocess.Popen('python3 q-learning.py', shell=True)
        process.wait()
    if lang == "sql":
        process = subprocess.Popen('sh ./execute_sqlite.sh', shell=True)
        process.wait()

    update_inputs(episodes=inputs[1], tries=inputs[2], epsilon=inputs[-1])
    compute_convergence(operation='compute')
    
def write_data(current_round, client_avg_worst, server_avg, end_of_round=False, vertical=False):
    if end_of_round:
        epsilon_val = read_inputs("data/inputs.csv")[-1]
        compute_convergence(operation='average', round=current_round, end_of_round=True)
        write_times(client_avg_worst, server_avg, end_of_round=True)
        if vertical and ((current_round - 1) % 5 ) == 0:
            update_inputs(epsilon = 0.5)
        elif epsilon_val > 0.01:
            update_inputs(epsilon = epsilon_val * 0.97)
    else:
        compute_convergence(operation='average', round=current_round)
        write_times(current_round, client_avg_worst, server_avg)
