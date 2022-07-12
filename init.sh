#!/bin/bash

sudo apt-get install -y python3-pip
pip3 install numpy seaborn

# https://github.com/nodesource/distributions/blob/master/README.md
sudo apt-get install -y curl
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install

cd public/data/
sh init.sh
cd ../..
