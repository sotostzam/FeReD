import sys
import csv
import os
import math
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib import cm
import numpy as np
import seaborn as sns
import warnings
warnings.simplefilter("ignore")

# Action icons for heatmaps
actions = {
    0: u"\u2190",
    1: u"\u2192",
    2: u"\u2191",
    3: u"\u2193"
}

# Custom cmaps for heatmaps
discrete_colors = ((1.0,1.0,1.0,1.0), (0.0,0.0,0.0,1.0), (1.0,0.0,0.0,1.0), (0.0,1.0,0.0,1.0))
maze_discrete = LinearSegmentedColormap.from_list('Custom', discrete_colors, len(discrete_colors))
extract_cmap = cm.get_cmap('RdGy_r')
modified_cmap = extract_cmap(np.linspace(0,1,256))
modified_cmap[:1,:] = np.array([0, 0, 0, 1])
enhanced_cmap = ListedColormap(modified_cmap)

def extract_policy(file_loc, mode=None, counter=None):
    '''
    Helper function to extract the policy matrix from a given file.

    Arguments:
        file_loc: Location of the file
        mode: (vertical/horizontal) based on data partitioning
        counter: Used only for vertical partitioning to identify the active partition layout
    Returns:
        q_table: Generated Q-table
        annot: Matrix with annotations
    '''
    with open(file_loc) as read_file:
        imported_table = list(csv.reader(read_file, delimiter=";"))
        size    = int(math.sqrt(len(imported_table)/4))
        if mode == "vertical":
            maze_file = np.genfromtxt(('federated_data/layouts/layout' + str(counter) + '.csv'), delimiter=',', dtype = int)
        else:
            maze_file = np.genfromtxt(('datasets/custom-maze_' + str(size) + '.csv'), delimiter=',', dtype = int)
        q_table = np.ones((size,size)) * -999
        annot   = np.full((size,size), actions[0], dtype='U1')
        for row in imported_table:
            vals = [int(row[0]), int(row[1]), int(row[2]), float(row[3])]
            if q_table[vals[0],vals[1]] < vals[3]:
                q_table[vals[0],vals[1]] = vals[3]
                annot[vals[0],vals[1]] = actions[vals[2]]
        if np.any(q_table):
            q_table = (q_table - np.min(q_table)) / np.ptp(q_table) # Normalize [0,1]
        for i in range(maze_file.shape[0]):
            for j in range(maze_file.shape[1]):
                if maze_file[i,j] == 1:
                    q_table[i,j] = -1
                    annot[i,j] = ""
                if maze_file[i,j] == 3:
                    annot[i,j] = u"\u2714"
        return q_table, annot

def plot_times():
    f = open ("results.txt")
    lines = []
    for l in f.readlines():
        l = l.strip().split(' ')
        lines.append([int(l[0]), int(l[1]), int(l[2]), float(l[3]), float(l[4])])
    
    lines = np.array(lines)
        
    ep_gen_vals = np.unique(lines[:,0], axis=0).astype(int)
    tr_gen_vals = np.unique(lines[:,1], axis=0).astype(int)
    sz_gen_vals = np.unique(lines[:,2], axis=0).astype(int)
    
    ep_vals = range(min(ep_gen_vals), max(ep_gen_vals)+1, (ep_gen_vals[1]-ep_gen_vals[0]))
    tr_vals = range(min(tr_gen_vals), max(tr_gen_vals)+1, (tr_gen_vals[1]-tr_gen_vals[0]))
    ms_vals = range(min(sz_gen_vals), max(sz_gen_vals)+1, (sz_gen_vals[1]-sz_gen_vals[0]))

    markers = ['s', 'o', 'x', 'd', '1']
    colors = ["magenta", "green"]
    font_size = 8
    marker_size = 10

    # Plot with varying Episodes
    plt.rcParams.update({'font.size':font_size})
    fixed_ms = 10
    for episode in list(reversed(tr_vals)):
        y_vals_P = []
        y_vals_S = []
        for line in lines:
            if line[1] == episode and line[2] == fixed_ms:
                y_vals_P.append(line[3])
                y_vals_S.append(line[4])
        plt.plot(ep_vals, y_vals_P, marker=markers[tr_vals.index(episode)], markersize=marker_size,
                 fillstyle='none', color=colors[0], label= "Python, Tr=%d, Ms=%d" % (episode, fixed_ms), linestyle="--")
        plt.plot(ep_vals, y_vals_S, marker=markers[tr_vals.index(episode)], markersize=marker_size,
                 fillstyle='none', color=colors[1], label= "SQLite, Tr=%d, Ms=%d" % (episode, fixed_ms))

    plt.gca().xaxis.set_ticks(ep_vals)
    plt.title("Varying episodes (Ep) for fixed tries (Tr) and maze size (Ms)", fontsize=font_size)
    plt.xlabel("Number of episodes")
    plt.ylabel("Time (seconds)")
    plt.legend(loc='upper left', ncol=2)
    plt.tight_layout()
    plt.savefig("plots/plot_varyEp.pdf")
    plt.clf()

    # Plot with varying tries
    plt.rcParams.update({'font.size':font_size})
    fixed_ms = 10
    for try_num in list(reversed(ep_vals)):
        y_vals_P = []
        y_vals_S = []
        for line in lines:
            if line[0] == try_num and line[2] == fixed_ms:
                y_vals_P.append(line[3])
                y_vals_S.append(line[4])

        plt.plot(tr_vals, y_vals_P, marker=markers[ep_vals.index(try_num)], markersize=marker_size,
                 fillstyle='none', color=colors[0], label= "Python, Ep=%d, Ms=%d" % (try_num, fixed_ms), linestyle="--")
        plt.plot(tr_vals, y_vals_S, marker=markers[ep_vals.index(try_num)], markersize=marker_size,
                 fillstyle='none', color=colors[1], label= "SQLite, Ep=%d, Ms=%d" % (try_num, fixed_ms))

    plt.gca().xaxis.set_ticks(tr_vals)
    plt.title("Varying tries (Tr) for fixed episodes (Ep) and maze size (Ms)", fontsize=font_size)
    plt.xlabel("Number of tries per episode")
    plt.ylabel("Time (seconds)")
    plt.legend(loc='upper left', ncol=2)
    plt.tight_layout()
    plt.savefig("plots/plot_varyTr.pdf")
    plt.clf()

    # Plot with varying maze size
    plt.rcParams.update({'font.size':font_size})
    i = 0 # for marker index
    for fixed_episode in [ep_vals[2], ep_vals[1]]:
        for fixed_try in [tr_vals[2], tr_vals[1]]:
            y_vals_P = []
            y_vals_S = []
            for line in lines:
                if line[0] == fixed_episode and line[1] == fixed_try:
                    y_vals_P.append(line[3])
                    y_vals_S.append(line[4])
    
            plt.plot(ms_vals, y_vals_P, marker=list(reversed(markers))[i], markersize=marker_size,
                     fillstyle='none', color=colors[0], label= "Python, Ep=%d, Tr=%d" % (fixed_episode, fixed_try), linestyle="--")
            plt.plot(ms_vals, y_vals_S, marker=list(reversed(markers))[i], markersize=marker_size,
                     fillstyle='none', color=colors[1], label= "SQLite, Ep=%d, Tr=%d" % (fixed_episode, fixed_try))
            i += 1

    plt.gca().xaxis.set_ticks(ms_vals)
    plt.title("Varying maze size (Ms) for fixed episodes (Ep) and tries (Tr)", fontsize=font_size)
    plt.xlabel("Maze size (Rows = Columns)")
    plt.ylabel("Time (seconds)")
    plt.legend(loc='upper left', ncol=2)
    plt.tight_layout()
    plt.savefig("plots/plot_varySz.pdf")
    plt.clf()

def generate_maze_layout(size):
    maze_file = np.genfromtxt(('datasets/custom-maze_' + str(size) + '.csv'), delimiter=',', dtype = int)
    fig = plt.figure(figsize=(5, 4))
    fig.tight_layout()
    ax = sns.heatmap(maze_file, linewidth=0.5, linecolor="black", clip_on=False, cmap=maze_discrete, cbar=True)

    colorbar = ax.collections[0].colorbar
    colorbar.set_ticks([0.35, 1.1, 1.9, 2.65])
    colorbar.set_ticklabels(['Path', 'Hole', 'Start', 'Goal'])
    colorbar.ax.tick_params(labelsize=18)
    colorbar.outline.set_linewidth(1)

    plt.savefig("./plots/maze_layout.png", bbox_inches = 'tight')

def plot_tables(mode=None, round=None):
    p_q_table, p_q_table_annot = extract_policy('results/qtable-python.csv')
    s_q_table, s_q_table_annot = extract_policy('results/qtable-sql.csv')

    # Plot best policy
    fig = plt.figure(figsize=(4, 4))
    fig.tight_layout()

    # Policy heatmap for Python
    sns.heatmap(p_q_table, linewidth=0.5, linecolor="black", clip_on=False,
                cmap=enhanced_cmap, cbar=False, annot=p_q_table_annot, fmt='')
    if mode == "experiment":
        plt.savefig("plots/experiment/policy_heatmap_python.png", bbox_inches = 'tight')
    elif mode == "initialize":
        plt.savefig("plots/round0/policy_heatmap_python.png", bbox_inches = 'tight')
    else:
        plt.savefig("plots/round" + str(round) + "/policy_heatmap_python.png", bbox_inches = 'tight')
    plt.clf()

    # Policy heatmap for SQLite
    sns.heatmap(s_q_table, linewidth=0.5, linecolor="black", clip_on=False,
                cmap=enhanced_cmap, cbar=False, annot=s_q_table_annot, fmt='')
    if mode == "experiment":
        plt.savefig("plots/experiment/policy_heatmap_sql.png", bbox_inches = 'tight')
    elif mode == "initialize":
        plt.savefig("plots/round0/policy_heatmap_sql.png", bbox_inches = 'tight')
    else:
        plt.savefig("plots/round" + str(round) + "/policy_heatmap_sql.png", bbox_inches = 'tight')
    
def plot_fltimes(mode=None):
    if mode == "initialize":
        x = [0, 1]
        lines = np.array([[0, 0, 0, 0, 0], [1, 0, 0, 0, 0]])
        limits = [1, 1]
        max_ylim = 1
    else:
        f = open ("./results/times.txt")
        lines = []
        for l in f.readlines():
            l = l.strip().split('\t')
            # Timings are as found: [Round, Client, Server]
            lines.append([int(l[0]), float(l[1]), float(l[2]), float(l[3]), float(l[4])])
        lines = np.array(lines)
        
        x = range(int(lines[0,0]), int(lines[-1,0])+1)
        limits = [lines[0,0], lines[-1,0]]
        max_val_python = max(lines[:,1]) + max(lines[:,2])
        max_val_sqlite = max(lines[:,3]) + max(lines[:,4])
        max_total = max(max_val_python, max_val_sqlite)
        max_ylim = max_total + (20 / 100) * max_total
    sns.set_theme()
    
    fig = plt.figure(figsize=(5.5, 4))
    fig.tight_layout()
    
    plt.stackplot(x, [lines[:,1], lines[:,2]], labels=['Client', 'Coordinator'])
    plt.xlim(limits)
    plt.ylim([0, max_ylim])
    plt.title('Python Latency')
    plt.xlabel("Rounds")
    plt.ylabel("Time (seconds)")
    plt.legend(loc='upper center', fontsize=13, ncol=2)
    if mode == "experiment":
        plt.savefig("plots/experiment/sync_times_python.png", bbox_inches = 'tight')
    elif mode == "initialize":
        plt.savefig("plots/round0/sync_times_python.png", bbox_inches = 'tight')
    else:
        plt.savefig("plots/round" + str(int(lines[-1, 0])) + "/sync_times_python.png", bbox_inches = 'tight')
    plt.clf()
    
    plt.stackplot(x, [lines[:,3], lines[:,4]], labels=['Client', 'Coordinator'])
    plt.xlim(limits)
    plt.ylim([0, max_ylim])
    plt.xlabel("Rounds")
    plt.ylabel("Time (seconds)")
    plt.title('SQLite Latency')
    plt.legend(loc='upper center', fontsize=13, ncol=2)
    if mode == "experiment":
        plt.savefig("plots/experiment/sync_times_sql.png", bbox_inches = 'tight')
    elif mode == "initialize":
        plt.savefig("plots/round0/sync_times_sql.png", bbox_inches = 'tight')
    else:
        plt.savefig("plots/round" + str(int(lines[-1, 0])) + "/sync_times_sql.png", bbox_inches = 'tight')

def plot_convergence(mode=None):
    if mode == "initialize":
        python_conv_fixed = np.ones((2, 1)) * -101
        sqlite_conv_fixed = np.ones((2, 1)) * -101
        x = [0, 1]
    else:
        f = open ("./results/convergence.txt")
        lines = []
        for l in f.readlines():
            l = l.strip().split('\t')
            lines.append([int(l[0]), float(l[1]), float(l[2])])
        lines = np.array(lines)
        
        x = lines[:,0].astype(int)
        python_conv_fixed = lines[:,1].astype(float)
        sqlite_conv_fixed = lines[:,2].astype(float)

    fig = plt.figure(figsize=(5.5, 4))
    fig.tight_layout()

    plt.plot(x, python_conv_fixed, label = "Python")
    plt.plot(x, sqlite_conv_fixed, label = "SQLite")
    if mode == "initialize":
        plt.xlim([1, 1])
        plt.ylim([-100, 100])
    else:
        plt.xlim([1, lines[-1, 0]])
    plt.title("Convergence Rate")
    plt.xlabel("Rounds")
    plt.ylabel("Best Reward")
    plt.legend(loc='lower right', fontsize=13)
    if mode == "experiment":
        plt.savefig("plots/experiment/convergence.png", bbox_inches = 'tight')
    elif mode == "initialize":
        plt.savefig("plots/round0/convergence.png", bbox_inches = 'tight')
    else:
        plt.savefig("plots/round" + str(int(lines[-1, 0])) + "/convergence.png", bbox_inches = 'tight')

def make_snapshot(format=None, round=None, mode=None, overall=False):
    if overall:
        plot_fltimes()
        plot_tables(round=round)
        plot_convergence()
    else:
        directory = "federated_data/policies"
        counter=1

        # Create snapshots of clients local models
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            if mode == "vertical":
                q_table, q_table_annot = extract_policy(f, mode="vertical", counter=counter)
            else:
                q_table, q_table_annot = extract_policy(f, mode="horizontal", counter=counter)
            fig = plt.figure(figsize=(4, 4))
            fig.tight_layout()
            sns.heatmap(q_table, linewidth=0.5, linecolor="black", clip_on=False,
                    cmap=enhanced_cmap, cbar=False, annot=q_table_annot, fmt='')
            plt.savefig("./plots/round" + str(round) + "/client_policy_heatmap_" + format + str(counter) + ".png",
                        bbox_inches = 'tight')
            plt.clf()
            counter += 1

        # Create snapshot of current global federated model
        if mode == "vertical":
            q_table, q_table_annot = extract_policy('data/global-qtable-' + format + '.csv')
        if mode == "horizontal":
            q_table, q_table_annot = extract_policy('results/qtable-' + format + '.csv')
        fig = plt.figure(figsize=(4, 4))
        fig.tight_layout()
        ax = sns.heatmap(q_table, linewidth=0.5, linecolor="black", clip_on=False,
                    cmap=enhanced_cmap, cbar=False, annot=q_table_annot, fmt='')

        plt.savefig("./plots/round" + str(round) + "/server_policy_heatmap_" + format + ".png",
                    bbox_inches = 'tight')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "initialize":
            plot_fltimes(mode="initialize")
            plot_convergence(mode="initialize")
            plot_tables(mode="initialize")
        if sys.argv[1] == "make_snapshot":
            make_snapshot(sys.argv[2], sys.argv[3], sys.argv[4])
        if sys.argv[1] == "times":
            plot_times()
    else:
        plot_fltimes(mode="experiment")
        plot_convergence(mode="experiment")
        plot_tables(mode="experiment")
