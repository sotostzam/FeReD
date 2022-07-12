import csv
import os
import time
import numpy as np
from utils import matrix_from_csv, export_to_csv, read_from_csv, write_times, update_inputs, find_next_candidate

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
        offset_i, offset_j, par_size = model[1]
        for i in range(client_qtable.shape[0]):
            for j in range(client_qtable.shape[1]):
                maze_pos_x = i + offset_i  # Map to position in global model
                maze_pos_y = j + offset_j  # Map to position in global model
                if not explored_states or [maze_pos_x, maze_pos_y] not in explored_states:
                    for k in range(client_qtable.shape[2]):
                        if client_qtable[i,j,k] != q_table[maze_pos_x, maze_pos_y, k]:
                            if (maze_pos_x, maze_pos_y, k) not in updates:
                                updates[(maze_pos_x, maze_pos_y, k)] = [client_qtable[i,j,k]]
                            else:
                                updates[(maze_pos_x, maze_pos_y, k)].append(client_qtable[i,j,k])

    # Average the updates
    for pos, values in updates.items():
        updates[pos] = sum(values) / len(values)

    target_min = 0
    target_max = max(q_table[candidate[0], candidate[1]]) - 0.001 * max(q_table[candidate[0], candidate[1]])
    if target_max == 0:
        target_max = 100
    update_min = min(updates.values())
    update_max = max(updates.values())
    for pos, values in updates.items():
        #q_table[pos[0],pos[1],pos[2]] = sum(values) / len(values)
        #temp = sum(values) / len(values)
        new_val = ((values - update_min)/(update_max - update_min)) * (target_max - target_min) + target_min
        q_table[pos[0],pos[1],pos[2]] = new_val
    
    # Update global federated model
    export_to_csv("data/global-qtable-" + format + ".csv", q_table)

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
