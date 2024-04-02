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

@app.route('/brokers', methods=['POST'])
def get_data_brokers():
    print("reciever data from client :",request.data.decode())
    votes = set_votes()
    set_current_log(str(request.data.decode()))
    for peer in node.peers.values():
        url = 'http://127.0.1.1:'+str(int(peer.port)+1)+'/fromLeader'
        try:
            log_id = int(get_current_log_id())+1
            final_data = str(log_id)+request.data.decode()
            final_data = bytes(final_data,'ascii')
            r = requests.post(url=url, data=final_data)
            print("leader",votes)
            time.sleep(1)
        except:
            print("not able to forward message to follower",peer.nid)
    
    return Response('We recieved something…')
@app.route('/confirmation',methods=['POST','GET'])
def leader_confirm():
    print("confirmation from followers :",request.data.decode())
    no_of_nodes = 1 +len(node.peers)
    print(no_of_nodes)
    votes =increament_votes()
    data = get_current_log()
    if votes >no_of_nodes-1 :# count the no of nodes and make it generalized 
        log_id = increament_current_log_id()
        final_data = 'Log Id ('+str(log_id)+') : '+data
        filename = 'log'+str(node.nid)+'.txt'
        file = open(filename, "a")  # append mode
        file.write(str(final_data))
        file.close()
        # print("commit action")
    # print("confirmed action",request.data,"votes = ",votes)
    return Response('We recieved something…')
def set_log_id():
    filename = 'log'+str(node.nid)+'.txt'
    with open(filename, 'r') as file:
        lines = file.read().splitlines()
        try:
            last_line = lines[-1]
        except:
            return 0
        print (last_line)
    if last_line == '':
        return 0
    else:
        return last_line[8]

@app.route('/fromLeader', methods=['POST'])
def get_data_leader():
    print("recieved message from leader :",request.data.decode())
    
    for peer in node.peers.values():
        if(peer.state =='l'):
            url = 'http://127.0.1.1:'+str(int(peer.port)+1)+'/confirmation'
            data = b'data recieved action'
            # try:
            r = requests.post(url=url, data=data)
            id = set_log_id()
            update_log_id(id)
            log_id = int(get_current_log_id())+1
            # print("data recieved ",request.data.decode(),int(request.data.decode()[0])," == ",log_id)
            if int(request.data.decode()[0]) == log_id:
                final_data = 'Log Id ('+str(log_id)+') : '+str(request.data.decode()[1:])
                filename = 'log'+str(node.nid)+'.txt'
                file = open(filename, "a")  # append mode
                file.write(final_data)
                file.close()
                increament_current_log_id()
            elif int(request.data.decode()[0]) > log_id:
                print("request for more data")
            else:
                print("waiting for sync...")

    return Response('We recieved something…')

def leader_run_action(node):

    def ping():
        while not node.shutdown_flag:
            time.sleep(2)
            print("I am leader",node.state)
            for peer in node.peers.values():
                # print("peer-address",peer.addr)
                url = 'http://127.0.1.1:'+str(int(peer.port)+1)
                data = b'leader is alive'
    
    x1 = threading.Thread(target=ping)
    x1.start()
    x1.join()


