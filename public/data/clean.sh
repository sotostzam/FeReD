#!/bin/bash

rm -rf ./data/*
rm -rf ./plots/*
rm -rf ./results/*
rm -rf ./federated_data/*

mkdir -p federated_data/policies
mkdir -p federated_data/rewards
mkdir -p federated_data/convergence_vals
mkdir -p federated_data/global_tables
mkdir -p federated_data/partitions
mkdir -p federated_data/layouts
