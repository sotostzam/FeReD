#!/bin/bash

mkdir -p experiments
rm -rf ./experiments/*

size=15
rounds=(50 100 200)
clients=(5 25)
episodes=(1 10 25)
tries=(50 100 200)
learning_rate=0.05
modes=(0 1 2)
par_size=(5 10)
experiment_number=0
n_experiments=$(echo "${#rounds[@]} * ${#clients[@]} * ${#episodes[@]} * ${#tries[@]} * (${#modes[@]} + ${#par_size[@]})" | bc -l | sed 's/^\./0./')

for round in ${rounds[@]}; do
  for n_clients in ${clients[@]}; do
    for n_episodes in ${episodes[@]}; do
      for n_tries in ${tries[@]}; do

        # Horizontal partitioning of data experiments
        for mode in ${modes[@]}; do
          experiment_number=$(echo "$experiment_number + 1" | bc -l | sed 's/^\./0./')
          echo "Experiment number: $experiment_number/$n_experiments"
          echo -e "Parameters: HFRL, $round F_rounds, $n_clients Clients, $n_episodes Episodes, $n_tries Length, Mode $mode\n"
          bash start-api.sh "apply-model" $size "horizontal" $round $n_clients -1 $n_episodes $n_tries $learning_rate $mode 1
          bash start-api.sh "run-model" $size "horizontal" $round $n_clients -1 $n_episodes $n_tries $learning_rate $mode 1
        done

        # Vertical partitioning of data experiments
        for partition_size in ${par_size[@]}; do
          experiment_number=$(echo "$experiment_number + 1" | bc -l | sed 's/^\./0./')
          echo "Experiment number: $experiment_number/$n_experiments"
          echo -e "Parameters: VFRL, $round F_rounds, $n_clients Clients, $n_episodes Episodes, $n_tries Length, Partition Size $partition_size\n"
          bash start-api.sh "apply-model" $size "vertical" $round $n_clients $partition_size $n_episodes $n_tries $learning_rate -1 1
          bash start-api.sh "run-model" $size "vertical" $round $n_clients $partition_size $n_episodes $n_tries $learning_rate -1 1
        done

      done   # number of tries loop
    done     # number of episodes loop
  done       # clients loop
done         # federated rounds loop
