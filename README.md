# FeReD

![fered](/public/assets/fered.jpeg)

This repository contains code for **FeReD**, a system that contrasts the performance of cross-device federation using *Q-learning*, a popular reinforcement learning algorithm. **FeReD** offers step-by-step guidance for in-DBMS SQLite implementation challenges for both horizontal and vertical data partitioning. **FeReD** also allows to contrast the *Q-learning* implementations in SQLite vs a standard Python implementation, by highlighting their learning performance, computational efficiency, succinctness and expressiveness.

## Structure

FeRed is a web **interface** that allows a user to perform experiments with various parameters using Q-learning. The root folder contains code the back-end **NodeJS** codebase. The folder */public/* contains the files related to the web interface, while */public/data* contains the code specific to the implementation of Q-learning algorithms in both Python and SQLite.

The most notable files are the following:

* `/app.js` contains the code for the Node.js back-end server.
* `/public/data/start-api.sh` contains the logic to run models in horizontal/vertical data partitioning.
* `/public/data/start-experiments.sh` contains code to run automated experiments with various configurations.
* `/public/data/q-learning.py` and `/public/data/q-learning.py` contain the Q-learning algorithms.

## Requirements

1. Python 3
2. Numpy
3. Seaborn and Matplotlib
4. Node.js and npm

## Usage

1. Download code.
2. Install required libraries and tools by running `bash init.sh` in a terminal.
3. Start API using `node app.js`.
4. Open [http://localhost:8080/](http://localhost:8080/) in your browser.

### In order to run the automated experiments

1. In a terminal `cd public/data`.
2. Use `bash start-experiments.sh` to run the code.

## Team

![sotiris](/public/assets/sotiris.png) | ![radu](/public/assets/radu.png) | ![marta](/public/assets/marta.jpg) | ![sihem](/public/assets/sihem.jpg)
------------ | ------------- | ------------- | -------------
[Sotirios Tzamaras](https://www.linkedin.com/in/sotiris-tzamaras/) | [Radu Ciucanu](https://lig-membres.imag.fr/ciucanu/) | [Marta Soare](https://lig-membres.imag.fr/soare/) | [Sihem Amer-Yahia](https://lig-membres.imag.fr/amery/)
