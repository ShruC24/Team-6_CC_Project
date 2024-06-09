# Updated RaftNode file with streamlit and MySQL integration

import time
import threading
from pyraft import raft
from flask import Flask, Response, request, copy_current_request_context, jsonify
import sys
import requests
from flask_cors import CORS
import logging
import mysql.connector


# Create MySQL connection
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="mysql#3",
    database="TASK_MANAGEMENT"
)

cursor = db_connection.cursor()

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
    current_log_id += 1
    return current_log_id

def get_latest_data():
    sql = 'SELECT * FROM tasks ORDER BY task_id DESC LIMIT 1'
    cursor.execute(sql)
    latest_data = cursor.fetchone()
    if latest_data:
        # Assuming the data structure returned from the database is known
        task_id, title, task_status, created_by = latest_data
        return jsonify({
            'TASK_ID': task_id,
            'TITLE': title,
            'TASK_STATUS': task_status,
            'CREATED_BY': created_by
        })
    else:
        return jsonify({'error': 'No data found'}), 404

@app.route('/get_latest_data', methods=['GET'])
def get_latest_data_endpoint():
    return get_latest_data()

def get_tasks_from_db():
    sql = 'SELECT * FROM tasks'
    cursor.execute(sql)
    tasks = cursor.fetchall()
    return tasks

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
            print("leader", votes)
            time.sleep(1)
        except:
            print("not able to forward message to follower", peer.nid)

    return jsonify({'message': 'Data sent to followers'})

@app.route('/confirmation', methods=['POST', 'GET'])
def leader_confirm():
    print("confirmation from followers:", request.data.decode())
    no_of_nodes = 1 + len(node.peers)
    votes = increment_votes()
    data = get_current_log()
    if votes > no_of_nodes - 1:
        log_id = increment_current_log_id()
        final_data = 'Log Id (' + str(log_id) + ') : ' + data

    tasks = get_tasks_from_db()
    return jsonify(tasks)

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
    print("Received message from leader:", request.data.decode())

    try:
        data = request.json
    except ValueError:
        return jsonify({'error': 'Invalid JSON format'}), 400

    title = data.get('TITLE')
    task_status = data.get('TASK_STATUS')
    created_by = data.get('CREATED_BY')

    if title is None or task_status is None or created_by is None:
        return jsonify({'error': 'Missing required fields'}), 400

    sql = 'INSERT INTO tasks (TITLE, TASK_STATUS, CREATED_BY) VALUES (%s, %s, %s)'
    cursor.execute(sql, (title, task_status, created_by))
    db_connection.commit()

    for peer in node.peers.values():
        if peer.state == 'l':
            url = 'http://127.0.1.1:' + str(int(peer.port) + 1) + '/confirmation'
            try:
                r = requests.post(url=url, json=data)
                id = set_log_id()
                update_log_id(id)
                log_id = int(get_current_log_id()) + 1
                if int(request.data.decode()[0]) == log_id:
                    final_data = 'Log Id (' + str(log_id) + ') : ' + str(request.data.decode()[1:])
                    filename = 'log' + str(node.nid) + '.txt'
            except Exception as e:
                return jsonify({'error': 'Error sending confirmation to leader: ' + str(e)}), 500

    return jsonify({'message': 'Task created successfully'}), 201

@app.route('/fromLeader/<int:id>', methods=['PUT'])
def update_task(id):
    if node.state != 'l':
        return jsonify({'error': 'Only the leader node can perform delete operation'}), 403
    data = request.json
    title = data.get('TITLE')
    task_status = data.get('TASK_STATUS')
    created_by = data.get('CREATED_BY')

    set_clause = []
    values = []

    if title is not None:
        set_clause.append('TITLE = %s')
        values.append(title)

    if task_status is not None:
        set_clause.append('TASK_STATUS = %s')
        values.append(task_status)

    if created_by is not None:
        set_clause.append('CREATED_BY = %s')
        values.append(created_by)

    if not set_clause:
        return jsonify({'error': 'No fields provided for update'}), 400

    sql = 'UPDATE tasks SET ' + ', '.join(set_clause) + ' WHERE task_id = %s'
    values.append(id)

    cursor.execute(sql, tuple(values))
    db_connection.commit()

    # Propagate changes to followers
    for peer in node.peers.values():
        if peer.state != 'l':  # Only propagate changes to followers
            url = f'http://127.0.1.1:{int(peer.port) + 1}/confirmation'
            try:
                r = requests.put(url=url, json=data)
            except Exception as e:
                return jsonify({'error': 'Error sending update to follower: ' + str(e)}), 500

    return jsonify({'message': 'Task updated successfully and changes propagated to followers'}), 201


@app.route('/fromLeader/<int:id>', methods=['DELETE'])
def delete_task(id):
    if node.state != 'l':
        return jsonify({'error': 'Only the leader node can perform delete operation'}), 403

    # If the node is the leader, execute the delete operation
    sql = 'DELETE FROM tasks WHERE TASK_ID = %s'
    cursor.execute(sql, (id,))
    db_connection.commit()

    # Send confirmation to followers
    for peer in node.peers.values():
        if peer.state == 'l':
            url = 'http://127.0.1.1:' + str(int(peer.port) + 1) + '/confirmation'
            try:
                r = requests.post(url=url)
            except Exception as e:
                return jsonify({'error': 'Error sending confirmation to leader: ' + str(e)}), 500

    return jsonify({'message': 'Task deleted successfully'}), 201




def leader_run_action(node):
    def ping():
        while not node.shutdown_flag:
            time.sleep(2)
            print("I am leader", node.state)
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
    def ping():
        while not node.shutdown_flag:
            time.sleep(2)
            print("I am follower", node.state)
            for peer in node.peers.values():
                if peer.state == 'l':
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
    if get_server_running() == False:
        app.run(debug=False, port=port, host='127.0.1.1')

x4 = threading.Thread(target=start_server)
x4.start()

node.worker.handler['on_leader'] = leader_callback
node.worker.handler['on_follower'] = follower_callback

node.start()
node.join()
