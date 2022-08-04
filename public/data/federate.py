import csv
import os
from utils import matrix_from_csv, export_to_csv, read_from_csv
import numpy as np

# Manhattan distance of two points
def man_distance(point1, point2):
    return abs(point1[0]-point2[0])+abs(point1[1]-point2[1])
       
# Derivative of the sigmoid function 
def sig_deriv(z):
    a = 2
    b = 1.5
    sig = a / (1 + np.exp(-b*z))
    return sig * (a - sig)

# Normalization function
def normalize_range(current_min, current_max, target_min, target_max, value):
    return ((value - current_min) / (current_max - current_min)) * (target_max - target_min) + target_min   
        
# Compute average federated table from clients
def aggregate(format):

    # Load global model into memory
    q_table = matrix_from_csv('results/qtable-' + format + '.csv')

    # Load client's models into memory
    directory = "federated_data/policies"
    updates = {}
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        client_qtable = matrix_from_csv(f)

        # Perform aggregation
        for i in range(client_qtable.shape[0]):
            for j in range(client_qtable.shape[1]):
                for k in range(client_qtable.shape[2]):
                    if client_qtable[i,j,k] != q_table[i,j,k]:
                        if (i, j, k) not in updates:
                            updates[(i,j,k)] = [client_qtable[i,j,k]]
                        else:
                            updates[(i,j,k)].append(client_qtable[i,j,k])

    # Average athe updates
    for pos, values in updates.items():
        q_table[pos[0],pos[1],pos[2]] = sum(values) / len(values)

    # Update global federated model
    export_to_csv("results/qtable-" + format + ".csv", q_table)

def aggregate_vertical(format):

    # Load global model into memory
    q_table = matrix_from_csv("data/global-qtable-" + format + ".csv")

    # Load explored states and current candidate in memory
    candidate = read_from_csv("data/candidate-" + format + ".csv")
    explored_states = []
    with open("data/explored-states-" + format + ".csv") as f:
        vals = list(csv.reader(f, delimiter=";"))
        for val in vals:
            explored_states.append([int(val[0]), int(val[1])])

    # Load client's models into memory
    policies_path = "federated_data/policies"
    partitions_path = "federated_data/partitions/partition"
    client_partitions = {}
    for filename in os.listdir(policies_path):
        f = os.path.join(policies_path, filename)
        client_id = int(filename[6:-4])
        client_partitions[client_id] = [matrix_from_csv(f), read_from_csv(partitions_path + str(client_id) + ".csv")]

    # Perform aggregation
    updates = {}
    for _ , model in client_partitions.items():
        client_qtable = model[0]
        offset_i, offset_j, _ = model[1]
        for i in range(client_qtable.shape[0]):
            for j in range(client_qtable.shape[1]):
                maze_pos_x = i + offset_i  # Map to position in global model
                maze_pos_y = j + offset_j  # Map to position in global model
                if [maze_pos_x, maze_pos_y] != candidate and (not explored_states or [maze_pos_x, maze_pos_y] not in explored_states):
                    for k in range(client_qtable.shape[2]):
                        if client_qtable[i,j,k] != q_table[maze_pos_x, maze_pos_y, k]:
                            if (maze_pos_x, maze_pos_y, k) not in updates:
                                updates[(maze_pos_x, maze_pos_y, k)] = [client_qtable[i,j,k]]
                            else:
                                updates[(maze_pos_x, maze_pos_y, k)].append(client_qtable[i,j,k])

    # Average the updates
    for pos, values in updates.items():
        updates[pos] = sum(values) / len(values)

    # Normalize parameters
    target_min = 0
    target_max = max(q_table[candidate[0], candidate[1]]) - 0.01 * max(q_table[candidate[0], candidate[1]])
    if target_max == 0:
        target_max = 100
    update_min = min(updates.values())
    update_max = max(updates.values())
    
    # Update weighted Q-values with distance and activation
    for pos, values in updates.items():
        new_val = normalize_range(update_min, update_max, target_min, target_max, values)
        multiplier = sig_deriv(man_distance(pos, candidate) - 1)
        q_table[pos[0],pos[1],pos[2]] = new_val * multiplier
    
    # Update global federated model
    export_to_csv("data/global-qtable-" + format + ".csv", q_table)
