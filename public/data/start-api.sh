#!/bin/bash

size=$1
partition=$2
rounds=$3
clients=$4
par_size=$5
episodes=$6
tries=$7
learning_rate=$8
egreedy=$9
mode=${10}
tests=${11}

sh clean.sh    # Clean old files if they exist

# Initialize default plots and run models
if [ $partition == "horizontal" ]; then
  # Initialize required files for the horizontal partitioning
  if [ $tests -eq 2 ]; then
    python3 -c "from utils import prepare; prepare(partition='horizontal')" $episodes $tries $size $learning_rate 0
  else
    python3 -c "from utils import prepare; prepare(partition='horizontal')" $episodes $tries $size $learning_rate $egreedy
  fi
  if [ $tests -eq 0 ]; then
    python3 -c "from plot import generate_maze_layout; generate_maze_layout($size)"
  fi
  cp ./data/qtable.csv ./results/qtable-sql.csv                  # Create initial Q-table for SQLite
  cp ./data/qtable.csv ./results/qtable-python.csv               # Create initial Q-table for Python
  cp ./data/agent.csv ./data/agent-fixed.csv                     # Create backup for fixed agent position used in computing convergence
  touch ./results/times.txt                                      # Create file containing time measurements
  touch ./results/convergence.txt                                # Create file containing convergence rate values
else
  # Initialize required files for the vertical partitioning
  python3 -c "from utils import prepare; prepare(partition='vertical')" $episodes $tries $size $learning_rate $egreedy
  if [ $tests -eq 0 ]; then
    python3 -c "from plot import generate_maze_layout; generate_maze_layout($size)"
  fi
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
if [ $tests -eq 0 ]; then
  mkdir -p ./plots/round0              # Create directory to hold initial figures
  python3 plot.py "initialize" $rounds # Create initial plots and figures
else
  mkdir -p ./plots/experiment
fi

# Zero indicates that model preparation is completed
if [ $tests -eq 0 ]; then
  echo "0"
fi

if [ $partition == "horizontal" ]; then
  if [ $tests -eq 1 ]; then
    bash frl_horizontal.sh $clients $rounds $mode $episodes $tries $size $learning_rate $tests 100
    if [ $(ls -A "./plots/experiment" | wc -l) -ne 0 ]; then
      mkdir -p "./experiments/HFRL_r${rounds}_s${size}_c${clients}_e${episodes}_t${tries}_m${mode}"
    fi
    mv ./plots/experiment/* $_
  else
    bash frl_horizontal.sh $clients $rounds $mode $episodes $tries $size $learning_rate $tests 1
  fi
else
  if [ $tests -eq 1 ]; then
    bash frl_vertical.sh $clients $rounds $par_size $episodes $tries $size $learning_rate $tests 100
    if [ $(ls -A "./plots/experiment" | wc -l) -ne 0 ]; then
      mkdir -p "./experiments/VFRL_r${rounds}_s${size}_c${clients}_e${episodes}_t${tries}_p${par_size}"
    fi
    mv ./plots/experiment/* $_
  else
    bash frl_vertical.sh $clients $rounds $par_size $episodes $tries $size $learning_rate $tests 1
  fi
fi
