import csv
import os
from utils import matrix_from_csv, export_to_csv, read_from_csv
        
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
        q_table[pos[0],pos[1],pos[2]] = sum(values) / len(values)
    
    # Update global federated model
    export_to_csv("data/global-qtable-" + format + ".csv", q_table)
