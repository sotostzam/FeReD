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
test_num=0
n_tests=$(echo "${#rounds[@]} * ${#clients[@]} * ${#episodes[@]} * ${#tries[@]} * (${#modes[@]} + ${#par_size[@]})" | bc -l | sed 's/^\./0./')

n_test_dirs=0
test_success=0

echo -e "Total number of simulations: $n_tests\n"

# Experiments wih varying parameters
for round in ${rounds[@]}; do
  for n_clients in ${clients[@]}; do
    for n_episodes in ${episodes[@]}; do
      for n_tries in ${tries[@]}; do

        # Horizontal partitioning of data experiments
        for mode in ${modes[@]}; do
          test_num=$(echo "$test_num + 1" | bc -l | sed 's/^\./0./')
          echo -ne "\r\e[KSimulation $test_num/$n_tests: HFRL, $round F_rounds, $n_clients Clients, $n_episodes Episodes, $n_tries Length, Mode $mode"
          bash start-api.sh $size "horizontal" $round $n_clients -1 $n_episodes $n_tries $learning_rate 1 $mode 1
          
          n_test_dirs=$(find ./experiments -mindepth 1 -maxdepth 1 -type d | wc -l )
          if [ $n_test_dirs -gt $test_success ]; then
            test_success=$(echo "$test_success + 1" | bc -l | sed 's/^\./0./')
          fi
        done

        # Vertical partitioning of data experiments
        for par_sz in ${par_size[@]}; do
          test_num=$(echo "$test_num + 1" | bc -l | sed 's/^\./0./')
          echo -ne "\r\e[KSimulation $test_num/$n_tests: VFRL, $round F_rounds, $n_clients Clients, $n_episodes Episodes, $n_tries Length, Partition Size $par_sz"
          bash start-api.sh $size "vertical" $round $n_clients $par_sz $n_episodes $n_tries $learning_rate 0.8 -1 1
          
          n_test_dirs=$(find ./experiments -mindepth 1 -maxdepth 1 -type d | wc -l )
          if [ $n_test_dirs -gt $test_success ]; then
            test_success=$(echo "$test_success + 1" | bc -l | sed 's/^\./0./')
          fi
        done

      done   # number of tries loop
    done     # number of episodes loop
  done       # clients loop
done         # federated rounds loop

tests_failed=$(echo "$n_tests - $test_success" | bc -l | sed 's/^\./0./')
echo -e "\n\nSimulations: $test_success successful | $tests_failed failed | $n_tests total"

# Equality test
bash start-api.sh 15 "horizontal" 5 5 -1 10 100 $learning_rate 0 0 2
python3 -c "from utils import compare_equality; compare_equality()"
