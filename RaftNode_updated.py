import time
import threading
from pyraft import raft
from flask import Flask, Response, request
import requests
from flask_cors import CORS

votes = 0
current_log_info = ''
current_log_id = 0
server_running = False

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

def increment_votes():
    global votes
    votes += 1
    return votes

def set_votes():
    global votes
    votes = 1
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

def get_current_log_id():
    global current_log_id
    return current_log_id

def increment_current_log_id():
    global current_log_id
    current_log_id = int(current_log_id)
    current_log_id += 1
    return current_log_id

@app.route('/brokers', methods=['POST'])
def get_data_brokers():
    print("receiver data from client:", request.data.decode())
    votes = set_votes()
    set_current_log(str(request.data.decode()))
    for peer in node.peers.values():
        url = 'http://127.0.1.1:' + str(int(peer.port) + 1) + '/fromLeader'
        try:
            log_id = int(get_current_log_id()) + 1
            final_data = str(log_id) + request.data.decode()
            final_data = bytes(final_data, 'ascii')
            r = requests.post(url=url, data=final_data)
            print("I am", node.nid, node.state)
            time.sleep(1)
        except Exception as e:
            print("not able to forward message to follower", peer.nid, e)
    
    return Response('We received something…')

@app.route('/confirmation', methods=['POST', 'GET'])
def leader_confirm():
    print("confirmation from followers:", request.data.decode())
    no_of_nodes = 1 + len(node.peers)
    print(no_of_nodes)
    votes = increment_votes()
    data = get_current_log()
    if votes > no_of_nodes - 1: 
        log_id = increment_current_log_id()
        final_data = 'Log Id (' + str(log_id) + ') : ' + data
        filename = 'log' + str(node.nid) + '.txt'
        with open(filename, "a") as file:
            file.write(str(final_data))
    return Response('We received something…')

def set_log_id():
    filename = 'log' + str(node.nid) + '.txt'
    with open(filename, 'r') as file:
        lines = file.read().splitlines()
        try:
            last_line = lines[-1]
        except:
            return 0
        print(last_line)
    if last_line == '':
        return 0
    else:
        return last_line[8]

@app.route('/fromLeader', methods=['POST'])
def get_data_leader():
    print("received message from leader:", request.data.decode())
    for peer in node.peers.values():
        if(peer.state == 'l'):
            url = 'http://127.0.1.1:' + str(int(peer.port) + 1) + '/confirmation'
            data = b'data received action'
            try:
                r = requests.post(url=url, data=data)
                id = set_log_id()
                update_log_id(id)
                log_id = int(get_current_log_id()) + 1
                if int(request.data.decode()[0]) == log_id:
                    final_data = 'Log Id (' + str(log_id) + ') : ' + str(request.data.decode()[1:])
                    filename = 'log' + str(node.nid) + '.txt'
                    with open(filename, "a") as file:
                        file.write(final_data)
                    increment_current_log_id()
                elif int(request.data.decode()[0]) > log_id:
                    print("request for more data")
                else:
                    print("waiting for sync...")
            except Exception as e:
                print("Error:", e)

def leader_run_action(node):
    node.state = 'l'
    def ping():
        while not node.shutdown_flag:
            time.sleep(2)
            print("I am", node.nid, node.state)
            for peer in node.peers.values():
                url = 'http://127.0.1.1:' + str(int(peer.port) + 1)
                data = b'leader is alive'

    x1 = threading.Thread(target=ping)
    x1.start()
    x1.join()

def leader_callback(node):
    print('starting...')
    node = threading.Thread(target=leader_run_action, args=(node,))
    node.start()

def follower_run_action(node):
    node.state = 'f'
    def ping():
        while not node.shutdown_flag:
            time.sleep(2)
            print("I am", node.nid, node.state)
            for peer in node.peers.values():
                if(peer.state == 'l'):
                    url = 'http://127.0.1.1:' + str(int(peer.port) + 1)
                    data = b'follower alive'

    x1 = threading.Thread(target=ping)
    x1.start()

def follower_callback(node):
    print('starting...')
    node = threading.Thread(target=follower_run_action, args=(node,))
    node.start()

node = raft.make_default_node()

port = int(node.port) + 1

def start_server():
    if not get_server_running():
        app.run(debug=False, port=port, host='127.0.1.1')

x4 = threading.Thread(target=start_server)
x4.start()

node.worker.handler['on_leader'] = leader_callback
node.worker.handler['on_follower'] = follower_callback

node.start()
node.join()