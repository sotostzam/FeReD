#!/bin/bash

# Federated Learning Parameters
clients=$1     # Data owners
rounds=$2      # Federated Iterations
part_size=$3   # Size of the partition window (client learning problem)

# Reinforcement Learning Parameters
ep=$4          # Number of episodes
tr=$5          # Number of tries per episode
sz=$6          # Maze size
lr=$7          # Learning rate

# Testing Parameters
tests=$8       # Allows for snapshots of client data at each round if tests are false
R=$9           # Number of runs for client and server computations

for round in `seq 1 $rounds`; do
  if [ $tests -eq 0 ]; then
    mkdir -p ./plots/round$round  # Create directory to hold per round figures
  fi

  if [ $(( (round - 1) % 5 )) -eq 0 ]; then
    python3 -c "from utils import find_next_candidate; find_next_candidate('python')"
    python3 -c "from utils import find_next_candidate; find_next_candidate('sql')"
  fi

  #------------------------- Python -------------------------#

  client_avg_worst=0.0
  server_avg=0.0

  # Loop for number of tests used in averaging results
  for i in `seq 1 $R`; do
    worst_time=0.0

    # Select the appropriate global Q-table for this run
    if [ $R -gt 1 ] && [ $round -gt 1 ]; then
      cp -a ./federated_data/global_tables/global-qtable-python$i.csv ./data/global-qtable-python.csv
    fi

    # Loop for number of clients
    for j in `seq 1 $clients`; do
      # Preprocessing: Export partition according to mode and choose as goal the best Q-value so far
      python3 -c "from utils import extract_partition; extract_partition($part_size, 'python')"
      
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
      mv ./federated_data/partitions/partition.csv ./federated_data/partitions/partition$j.csv
      mv ./federated_data/layouts/layout.csv ./federated_data/layouts/layout$j.csv
    done
    client_avg_worst=$(echo "($client_avg_worst + $worst_time)" | bc -l | sed 's/^\./0./')

    # Perform aggregation of client computations and update global model
    t_start=$(date +%s.%N)
    python3 -c "from federate import aggregate_vertical; aggregate_vertical('python')"
    t_end=$(date +%s.%N)
    elapsed=$(echo "($t_end - $t_start)" | bc -l | sed 's/^\./0./')
    server_avg=$(echo "($server_avg + $elapsed)" | bc -l | sed 's/^\./0./')
    if [ $R -gt 1 ]; then
      cp ./data/global-qtable-python.csv ./federated_data/global_tables/global-qtable-python$i.csv
    fi

    # Create a snapshot of the current round
    if [ $tests -eq 0 ] && [ $i -eq $R ]; then
      python3 plot.py "make_snapshot" "python" "$round" "vertical"
      rm -r ./federated_data/partitions/*
    fi

    # Remove output client models
    rm -r ./federated_data/policies/*
    rm -r ./federated_data/rewards/*

    # Compute the convergence of a fixed position
    cp ./data/global-qtable-python.csv ./results/qtable-python.csv
    cp ./data/global-goal.csv ./data/goal.csv
    cp ./data/global-rewards.csv ./data/rewards.csv
    cp ./data/global-agent.csv ./data/agent.csv
    python3 -c "from utils import fixed_compute; fixed_compute('python')"
    mv ./federated_data/convergence_vals/convergence.txt ./federated_data/convergence_vals/convergence$i.txt

    # Clean result files
    rm -r ./federated_data/policies/*
    rm -r ./federated_data/rewards/*
    rm -r ./federated_data/layouts/*

    # Re-initialize global Q-table for new runs
    if [ $R -gt 1 ] && [ $round -eq 1 ]; then
      cp -a ./data/global-qtable.csv ./data/global-qtable-python.csv
    fi

  done
  client_avg_worst=$(echo "$client_avg_worst/$R" | bc -l | sed 's/^\./0./')
  server_avg=$(echo "($server_avg/$R)" | bc -l | sed 's/^\./0./')

  # Write data for average convergence, preprocessing and client computations
  python3 -c "from utils import write_data; write_data($round, $client_avg_worst, $server_avg)"
  rm -r ./federated_data/convergence_vals/*

  #------------------------- SQLite -------------------------#

  client_avg_worst=0.0
  server_avg=0.0

  # Loop for number of tests used in averaging results
  for i in `seq 1 $R`; do
    worst_time=0.0

    # Select the appropriate global Q-table for this run
    if [ $R -gt 1 ] && [ $round -gt 1 ]; then
      cp -a ./federated_data/global_tables/global-qtable-sql$i.csv ./data/global-qtable-sql.csv
    fi

    # Loop for number of clients
    for j in `seq 1 $clients`; do
      # Preprocessing: Export partition according to mode and choose as goal the best Q-value so far
      python3 -c "from utils import extract_partition; extract_partition($part_size, 'sql')"
      
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
      mv ./federated_data/partitions/partition.csv ./federated_data/partitions/partition$j.csv
      mv ./federated_data/layouts/layout.csv ./federated_data/layouts/layout$j.csv
    done
    client_avg_worst=$(echo "($client_avg_worst + $worst_time)" | bc -l | sed 's/^\./0./')

    # Perform aggregation of client computations and update global model
    t_start=$(date +%s.%N)
    python3 -c "from federate import aggregate_vertical; aggregate_vertical('sql')"
    t_end=$(date +%s.%N)
    elapsed=$(echo "($t_end - $t_start)" | bc -l | sed 's/^\./0./')
    server_avg=$(echo "($server_avg + $elapsed)" | bc -l | sed 's/^\./0./')
    if [ $R -gt 1 ]; then
      cp ./data/global-qtable-sql.csv ./federated_data/global_tables/global-qtable-sql$i.csv
    fi

    # Create a snapshot of the current round
    if [ $tests -eq 0 ] && [ $i -eq $R ]; then
      python3 plot.py "make_snapshot" "sql" "$round" "vertical"
      rm -r ./federated_data/partitions/*
    fi

    # Remove output client models
    rm -r ./federated_data/policies/*
    rm -r ./federated_data/rewards/*

    # Compute the convergence of a fixed position
    cp ./data/global-qtable-sql.csv ./results/qtable-sql.csv
    cp ./data/global-goal.csv ./data/goal.csv
    cp ./data/global-rewards.csv ./data/rewards.csv
    cp ./data/global-agent.csv ./data/agent.csv
    python3 -c "from utils import fixed_compute; fixed_compute('sql')"
    mv ./federated_data/convergence_vals/convergence.txt ./federated_data/convergence_vals/convergence$i.txt

    # Clean result files
    rm -r ./federated_data/policies/*
    rm -r ./federated_data/rewards/*
    rm -r ./federated_data/layouts/*

    # Re-initialize global Q-table for new runs
    if [ $R -gt 1 ] && [ $round -eq 1 ]; then
      cp -a ./data/global-qtable.csv ./data/global-qtable-sql.csv
    fi

  done
  client_avg_worst=$(echo "$client_avg_worst/$R" | bc -l | sed 's/^\./0./')
  server_avg=$(echo "($server_avg/$R)" | bc -l | sed 's/^\./0./')

  # Write data for average convergence, preprocessing, client computations and reduce greedy value
  python3 -c "from utils import write_data; write_data($round, $client_avg_worst, $server_avg, end_of_round=True, vertical=True)"

  # Create a snapshot for sync times and convergence for this round
  if [ $tests -eq 0 ]; then
    python3 -c "from plot import make_snapshot; make_snapshot(round=$round, overall=True)"
  fi

  # Output current computed round
  if [ $tests -eq 0 ]; then
    echo -ne "\r$round"
  fi
done

# Extract trained models to results
cp ./data/global-qtable-python.csv ./results/qtable-python.csv
cp ./data/global-qtable-sql.csv ./results/qtable-sql.csv

# Export plots and figures of experiment
if [ $tests -eq 1 ]; then
  python3 plot.py
fi
