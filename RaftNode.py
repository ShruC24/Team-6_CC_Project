import time
import threading
from pyraft import raft
from flask import Flask, Response, request, copy_current_request_context, jsonify
import sys
import requests
from flask_cors import CORS
import logging

votes = 0
current_log_info = ''
current_log_id = 0
server_running = False
global app
app = Flask(__name__)
CORS(app)

def set_server_running():
    global server_running
    server_running = True
    return server_running
def get_server_running():
    global server_running
    return server_running
def update_log_id(id):
    global current_log_id 
    current_log_id = id
    return current_log_id
def increament_votes():
    global votes 
    votes +=1
    return votes
def set_votes():
    global votes 
    votes =1
    return votes
def get_votes():
    global votes
    return votes
def set_current_log(log):
    global current_log_info
    current_log_info = log
    return current_log_info
def get_current_log():
    global current_log_info
    return current_log_info
def get_current_log_id ():
    global current_log_id 
    return current_log_id
def increament_current_log_id():
    global current_log_id
    print(type(current_log_id))
    current_log_id = int(current_log_id)
    current_log_id += 1
    return current_log_id
