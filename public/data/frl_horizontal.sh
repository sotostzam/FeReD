#!/bin/bash

# Federated Learning Parameters
clients=$1     # Data owners
rounds=$2      # Federated Iterations
mode=$3        # Mode for random initial positions (0: off, 1: per round, 2: per client)

# Reinforcement Learning Parameters
ep=$4          # Number of episodes
tr=$5          # Number of tries per episode
sz=$6          # Maze size
lr=$7          # Learning rate
epsilon=$8     # Epsilon

# Testing Parameters
tests=$9       # Allows for snapshots of client data at each round if tests are false
R=${10}        # Number of runs for client and server computations

for round in `seq 1 $rounds`; do
  if [ $tests -eq 0 ]; then
    mkdir -p ./plots/round$round  # Create directory to hold per round figures
  fi
  
  # Preprocessing: Randomize initial agent position according to mode
  if [ $mode -eq 1 ]; then
    python3 -c "from utils import randomize_init_pos; randomize_init_pos()"
  fi

  #------------------------- Python -------------------------#
  
  client_avg_worst=0.0
  server_avg=0.0

  # Loop for number of tests used in averaging results
  for i in `seq 1 $R`; do
    worst_time=0.0

    # Loop for number of clients
    for j in `seq 1 $clients`; do
      # Select the appropriate global Q-table for this run
      if [ $R -gt 1 ] && [ $round -gt 1 ]; then
        cp -a ./federated_data/global_tables/qtable-python$i.csv ./results/qtable-python.csv
      fi

      # Preprocessing: Randomize initial agent position according to mode
      if [ $mode -eq 2 ]; then
        python3 -c "from utils import randomize_init_pos; randomize_init_pos()"
      fi

      # Clients update their received model locally and send back the results
      t_start=$(date +%s.%N)
      python3 q-learning.py
      t_end=$(date +%s.%N)
      elapsed=$(echo "($t_end - $t_start)" | bc -l | sed 's/^\./0./')
      if (( $(echo "$elapsed > $worst_time" | bc -l) )); then
        worst_time=$elapsed
      fi
      mv ./federated_data/policies/qtable.csv ./federated_data/policies/qtable$j.csv
      mv ./federated_data/rewards/best_reward.csv ./federated_data/rewards/best_reward$j.csv
    done
    client_avg_worst=$(echo "($client_avg_worst + $worst_time)" | bc -l | sed 's/^\./0./')

    # Perform aggregation of client computations and update global model
    t_start=$(date +%s.%N)
    python3 -c "from federate import aggregate; aggregate('python')"
    t_end=$(date +%s.%N)
    elapsed=$(echo "($t_end - $t_start)" | bc -l | sed 's/^\./0./')
    server_avg=$(echo "($server_avg + $elapsed)" | bc -l | sed 's/^\./0./')
    if [ $R -gt 1 ]; then
      cp ./results/qtable-python.csv ./federated_data/global_tables/qtable-python$i.csv
    fi

    # Create a snapshot of the current round
    if [ $tests -eq 0 ] && [ $i -eq $R ]; then
      #cp -a ./federated_data/policies/. ./plots/round$round
      python3 plot.py "make_snapshot" "python" "$round" "horizontal"
    fi

    # Remove output client models
    rm -r ./federated_data/policies/*
    rm -r ./federated_data/rewards/*

    # Compute the convergence of a fixed position
    if [ $mode -gt 0 ]; then
      cp ./data/agent.csv ./data/agent-temp.csv     # Create backup of current starting position when mode=1 or mode=2
      cp ./data/agent-fixed.csv ./data/agent.csv    # Make fixed starting position active to compute convergence
    fi
    python3 -c "from utils import update_inputs; update_inputs(episodes=1, tries=200, epsilon=0)"
    python3 q-learning.py
    python3 -c "from utils import update_inputs; update_inputs(episodes=$ep, tries=$tr, epsilon=$epsilon)"
    python3 -c "from federate import compute_convergence; compute_convergence(operation='compute')"
    mv ./federated_data/convergence_vals/convergence.txt ./federated_data/convergence_vals/convergence$i.txt

    # Clean results and restore starting position for this round when mode != 0
    rm -r ./federated_data/policies/*
    rm -r ./federated_data/rewards/*
    if [ $mode -gt 0 ]; then
      cp ./data/agent-temp.csv ./data/agent.csv     # Restore agent in case mode=1
    fi

    # Re-initialize global Q-table for new runs
    if [ $R -gt 1 ] && [ $round -eq 1 ]; then
      cp -a ./data/qtable.csv ./results/qtable-python.csv
    fi

  done
  client_avg_worst=$(echo "$client_avg_worst/$R" | bc -l | sed 's/^\./0./')
  server_avg=$(echo "($server_avg/$R)" | bc -l | sed 's/^\./0./')

  # Compute average convergence
  python3 -c "from federate import compute_convergence; compute_convergence(operation='average', round=$round)"
  rm -r ./federated_data/convergence_vals/*
  
  # Write timings for preprocessing and client computations to file
  python3 -c "from utils import write_times; write_times($round, $client_avg_worst, $server_avg)"
  
  #------------------------- SQLite -------------------------#

  client_avg_worst=0.0
  server_avg=0.0

  # Loop for number of tests used in averaging results
  for i in `seq 1 $R`; do
    worst_time=0.0

    # Loop for number of clients
    for j in `seq 1 $clients`; do
      # Select the appropriate global Q-table for this run
      if [ $R -gt 1 ] && [ $round -gt 1 ]; then
        cp -a ./federated_data/global_tables/qtable-sql$i.csv  ./results/qtable-sql.csv
      fi

      # Preprocessing: Randomize initial agent position according to mode
      if [ $mode -eq 2 ]; then
        python3 -c "from utils import randomize_init_pos; randomize_init_pos()"
      fi

      # Clients update their received model locally and send back the results
      t_start=$(date +%s.%N)
      sh ./execute_sqlite.sh
      t_end=$(date +%s.%N)
      elapsed=$(echo "($t_end - $t_start)" | bc -l | sed 's/^\./0./')
      if (( $(echo "$elapsed > $worst_time" | bc -l) )); then
        worst_time=$elapsed
      fi
      mv ./federated_data/policies/qtable.csv ./federated_data/policies/qtable$j.csv
      mv ./federated_data/rewards/best_reward.csv ./federated_data/rewards/best_reward$j.csv
    done
    client_avg_worst=$(echo "($client_avg_worst + $worst_time)" | bc -l | sed 's/^\./0./')

    # Perform aggregation of client computations and update global model
    t_start=$(date +%s.%N)
    python3 -c "from federate import aggregate; aggregate('sql')"
    t_end=$(date +%s.%N)
    elapsed=$(echo "($t_end - $t_start)" | bc -l | sed 's/^\./0./')
    server_avg=$(echo "($server_avg + $elapsed)" | bc -l | sed 's/^\./0./')
    if [ $R -gt 1 ]; then
      cp ./results/qtable-sql.csv ./federated_data/global_tables/qtable-sql$i.csv
    fi

    # Create a snapshot of the current round
    if [ $tests -eq 0 ] && [ $i -eq $R ]; then
      #cp -a ./federated_data/policies/. ./plots/round$round
      python3 plot.py "make_snapshot" "sql" "$round" "horizontal"
    fi

    # Remove output client models
    rm -r ./federated_data/policies/*
    rm -r ./federated_data/rewards/*

    # Compute the convergence of a fixed position
    if [ $mode -gt 0 ]; then
      cp ./data/agent.csv ./data/agent-temp.csv     # Create backup of current starting position when mode=1 or mode=2
      cp ./data/agent-fixed.csv ./data/agent.csv    # Make fixed starting position active to compute convergence
    fi
    python3 -c "from utils import update_inputs; update_inputs(episodes=1, tries=200, epsilon=0)"
    sh ./execute_sqlite.sh
    python3 -c "from utils import update_inputs; update_inputs(episodes=$ep, tries=$tr, epsilon=$epsilon)"
    python3 -c "from federate import compute_convergence; compute_convergence(operation='compute')"
    mv ./federated_data/convergence_vals/convergence.txt ./federated_data/convergence_vals/convergence$i.txt

    # Clean results and restore starting position for this round when mode != 0
    rm -r ./federated_data/policies/*
    rm -r ./federated_data/rewards/*
    if [ $mode -gt 0 ]; then
      cp ./data/agent-temp.csv ./data/agent.csv     # Restore agent in case mode=1
    fi

    # Re-initialize global Q-table for new runs
    if [ $R -gt 1 ] && [ $round -eq 1 ]; then
      cp -a ./data/qtable.csv ./results/qtable-sql.csv
    fi
  done
  client_avg_worst=$(echo "$client_avg_worst/$R" | bc -l | sed 's/^\./0./')
  server_avg=$(echo "($server_avg/$R)" | bc -l | sed 's/^\./0./')

  # Compute average convergence
  python3 -c "from federate import compute_convergence; compute_convergence(operation='average', round=$round, end_of_round=True)"
  rm -r ./federated_data/convergence_vals/*
  
  # Write timings for preprocessing and client computations to file
  python3 -c "from utils import write_times; write_times($client_avg_worst, $server_avg, end_of_round=True)"

  # Create a snapshot for sync times and convergence for this round
  if [ $tests -eq 0 ]; then
    python3 -c "from plot import make_snapshot; make_snapshot(round=$round, overall=True)"
  fi
  
  # Reduce epsilon-greedy value per federated round
  epsilon=$(echo "$epsilon * 0.97" | bc -l | sed 's/^\./0./')
  python3 -c "from utils import update_inputs; update_inputs(epsilon=$epsilon)"
  
  if [ $tests -eq 0 ]; then
    echo -ne "\r$round"
  fi
done

# Export plots and figures of experiment
if [ $tests -eq 1 ]; then
  python3 plot.py
fi
