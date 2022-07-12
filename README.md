# FeReD

![fered](/public/assets/fered.jpeg)

This repository contains code for **FeReD**, a system that contrasts the performance of cross-device federation using *Q-learning*, a popular reinforcement learning algorithm. **FeReD** offers step-by-step guidance for in-DBMS SQLite implementation challenges for both horizontal and vertical data partitioning. **FeReD** also allows to contrast the *Q-learning* implementations in SQLite vs a standard Python implementation, by highlighting their learning performance, computational efficiency, succinctness and expressiveness.

## Structure

FeRed is a web **interface** that allows a user to perform experiments with various parameters using Q-learning. The root folder contains code the back-end **NodeJS** codebase. The folder */public/* contains the files related to the web interface, while */public/data* contains the code specific to the implementation of Q-learning algorithms in both Python and SQLite.

The most notable files are the following:

* `/index.js` contains the code for the Node.js back-end.
* `/start-api.sh` contains the logic to run experiments in either horizontal or vertical partitioning of data.
* `/public/data/q-learning.py` and `/public/data/q-learning.py` contain the Q-learning algorithms.

## Requirements

1. Python 3
2. Numpy
3. Seaborn and Matplotlib
4. Node.js and npm

## Usage

1. Download code.
2. Install required libraries and tools by running `bash init.sh` in a terminal.
3. Start API using `node index.js`.
4. Open [http://localhost:8080/](http://localhost:8080/) in your browser.

## Team

![sotiris](/public/assets/sotiris.png) | ![radu](/public/assets/radu.png) | ![marta](/public/assets/marta.jpg) | ![sihem](/public/assets/sihem.jpg)
------------ | ------------- | ------------- | -------------
[Sotirios Tzamaras](https://scholar.google.fr/citations?hl=fr&user=sbOKfl8AAAAJ) | [Radu Ciucanu](https://lig-membres.imag.fr/ciucanu/) | [Marta Soare](https://lig-membres.imag.fr/soare/) | [Sihem Amer-Yahia](https://lig-membres.imag.fr/amery/)