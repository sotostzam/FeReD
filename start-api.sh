#!/bin/bash

cd public/data

size=$2
partition=$3
rounds=$4
clients=$5
par_size=$6
episodes=$7
tries=$8
learning_rate=$9
mode=${10}

echo "${mode}"

if [ $1 == "apply-model" ]; then
  sh clean.sh    # Clean old files if they exist

  # Initialize default plots and run models
  if [ $partition == "horizontal" ]; then
    # Initialize required files for the horizontal partitioning
    python3 -c "from utils import prepare; prepare(partition='horizontal')" $episodes $tries $size $learning_rate 1
    python3 -c "from plot import generate_maze_layout; generate_maze_layout($size)"
    cp ./data/qtable.csv ./results/qtable-sql.csv                  # Create initial Q-table for SQLite
    cp ./data/qtable.csv ./results/qtable-python.csv               # Create initial Q-table for Python
    cp ./data/agent.csv ./data/agent-fixed.csv                     # Create backup for fixed agent position used in computing convergence
    touch ./results/times.txt                                      # Create file containing time measurements
    touch ./results/convergence.txt                                # Create file containing convergence rate values
  else
    # Initialize required files for the vertical partitioning
    python3 -c "from utils import prepare; prepare(partition='vertical')" $episodes $tries $size $learning_rate 0.8
    python3 -c "from plot import generate_maze_layout; generate_maze_layout($size)"
    cp ./data/global-qtable.csv ./data/global-qtable-python.csv    # Create global q_table for python
    cp ./data/global-qtable.csv ./data/global-qtable-sql.csv       # Create global q_table for sql
    cp ./data/global-qtable.csv ./results/qtable-python.csv        # Copy initial Q-table for Python for initial visualization
    cp ./data/global-qtable.csv ./results/qtable-sql.csv           # Copy initial Q-table for SQLite for initial visualization
    touch ./results/times.txt                                      # Create file containing time measurements
    touch ./results/convergence.txt                                # Create file containing convergence rate values
    touch ./data/explored-states-python.csv
    touch ./data/explored-states-sql.csv
    touch ./data/candidate-python.csv
    touch ./data/candidate-sql.csv
  fi
  mkdir -p ./plots/round0              # Create directory to hold initial figures
  python3 plot.py "initialize" $rounds # Create initial plots and figures
fi

if [ $1 == "run-model" ]; then
  if [ $partition == "horizontal" ]; then
    bash frl_horizontal.sh $clients $rounds $mode $episodes $tries $size $learning_rate 1
  else
    bash frl_vertical.sh $clients $rounds $par_size $episodes $tries $size $learning_rate 1
  fi
fi
