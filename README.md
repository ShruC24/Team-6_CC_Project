# Building a Task Management Application with Raft Consensus Algorithm and MySQL

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Commands ](#commands-used)
## Introduction
A task management web application using Python’s Streamlit that performs CRUD operations to a backend MySQL database through HTTP requests (GET, PUT and
POST). This can be run on 3 nodes/terminals which communicate with each other and perform leader
election using the raft consensus algorithm.

## Features

1. Can Create, View, Update, and Delete various tasks using a Python's Streamlit web application that replicates the functioning of a distributed system.
2. When a node is elected leader, it can perform all 4 CRUD operations on the tasks while the follower nodes can only View/Read the tasks.
3. When a node is deleted, i.e. fails, another node is elected the leader which can perform all 4 CRUD operations whereas it could only View/Read earlier when it was a follower earlier.
4. This continues till a single candidate node is left. 

## Technologies Used
- Python
- MySQL
- Frontend - Streamlit

## Commands To Run
commands to run on individual terminals
1. python RaftNode.py -a 127.0.0.1:5010 -i 1 -e 2/127.0.0.1:5020,3/127.0.0.1:5030 
2. python RaftNode.py -i 2 -a 127.0.0.1:5020 -e 1/127.0.0.1:5010,3/127.0.0.1:5030 
3. python RaftNode.py -i 3 -a 127.0.0.1:5030 -e 1/127.0.0.1:5010,2/127.0.0.1:5020

4. streamlit run streamlit.py
   

By:
Shreya Joshi
Shruti C
Spoorthi Shivaprasad
Sragvi Anil Shetty
