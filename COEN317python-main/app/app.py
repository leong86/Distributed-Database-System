from flask import Flask, request, json, jsonify
import webbrowser
from flask_ngrok import run_with_ngrok
import requests
import pymysql
import time
from random import randint
from backend_functions import *
import threading

app = Flask(__name__)
#run_with_ngrok(app)

db = ''
my_addrP = ''
up_time = time.time()
isLeader = False
leader_addrP = ''
quarm_id = 0
assigned = 0
# for copies sharing the same data
map = [set(), set()] # index  0 or 1 for quarm then address
replica_number = 0
key = False
lock_holder = ""
lock_del = threading.Lock()
lock_save = threading.Lock()
write_transactions = []

write_transactions = []

# just a simple test api to ensure it is up and running
@app.route("/")
def index():
    print("Recieved")
    return "Welcome to the API"

# another simple api to see how one node views the network. It is important
# that all nodes have the same view
@app.route("/topology", methods=['POST'])
def topology():
    return {'global_map': [list(map[0]), list(map[1])], 'qid': quarm_id, 'leader': leader_addrP}

# updates its understanding of a network is a new node is added
@app.route("/add", methods=["POST"])
def add(): # add node to map
    global map
    data = request.get_json()
    temp_map = data['global_map']
    map[0] = set(temp_map[0])
    map[1] = set(temp_map[1])
    print(map)
    return {"message": 'Done'}, 200

# This connects the node into the network
@app.route("/connect", methods=['POST']) # accept connection
def connect():
    #try:
    global assigned, map
    data = request.get_json()
    if data['addrP'] not in map[0] and data['addrP'] not in map[1]:
        id = assigned%2
        assigned = id + 1
        map[id].add(data['addrP'])
        s = {'global_map': [list(map[0]), list(map[1])]}
        share_map(map, s)
    else:
        if data['addrP'] in map[0]:
            id = 0
        else:
            id = 1

    return {'global_map': [list(map[0]), list(map[1])], 'qid': id, 'leader': leader_addrP}, 200
    #except:
    #    return "error allowing connection"

# this just saves to one node, regular save will save to all nodes in group
@app.route("/savesync", methods=['POST'])
def savesync():
    return saveto(db, request.get_json(), quarm_id)

# If a node wants to join the distributed system, it asks an existing node to join.
# if no existing node is provided/known, it will act as the first node in the distributed system
@app.route("/join", methods=['POST'])
def join():
    global uptime, my_addrP, map, db, quarm_id, leader_addrP, assigned
    #try:
    data = request.get_json()
    my_addrP = data['my_addrP']
    db = data['db']

    try: # creates table is not already created
        conn = pymysql.connect(host=db,user='root',password='root')
        conn.cursor().execute('create database test')
    except:
        pass
    try:
        conn.cursor().execute('create table test.test_table (id INT PRIMARY KEY, name VARCHAR(255))')
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass

    try:
        addrP = data['addrP']
    except: # first node with no place to connect is the temporary leader
        global isLeader
        isLeader = True
        leader_addrP = my_addrP
        map[quarm_id].add(my_addrP)
        assigned = (assigned + 1)%2
        return {'result': "First node established"}

    send = {'addrP': my_addrP}
    print('asking to join')
    response = requests.post('http://' + addrP + '/connect', json = send)
    print("recv join resp")
    resp_data = response.json()
    temp_map = resp_data['global_map']
    map[0] = set(temp_map[0])
    map[1] = set(temp_map[1])
    quarm_id = resp_data['qid']
    leader_addrP = resp_data['leader']
    return {'global_map': [list(map[0]), list(map[1])], 'qid': quarm_id, "leader": leader_addrP}
    #except:
    #    return "error connecting"

# api to save data to the entire distributed system
@app.route("/save", methods=['POST'])
def save():
    global lock_save
    lock_save.acquire(timeout=5)
    try:
        result = safe_save(db, map, request.get_json(), quarm_id, my_addrP)
    finally:
        lock_save.release()
    return result

# only pulls from one node so, another node corrdiantes a final response
@app.route("/selectlocal", methods=['POST'])
def selectlocal():
    return select_local(db, request.get_json())

# pull from node and from another node in other quarm. This produceds the final result
@app.route("/select", methods=['POST'])
def select():
    return select_from_network(request.get_json(), quarm_id, map, db)

# only deletes form local db, another node must cordinate for data consistancy
@app.route("/localdelete", methods=['DELETE'])
def localdelete():
    return local_delete(db, request.get_json(), quarm_id, my_addrP)

# This api ensures data consistance on a delete.
# Additioanlly, it will rollback a parttial change if any error is detected
@app.route("/delete", methods=['DELETE'])
def delete():
    global lock_del, key
    lock_del.acquire(timeout=5)
    key = tell_lock(map, my_addrP, key) # tell other nodes that the key is used if not already used
    result = safe_delete(db, map, request.get_json(), quarm_id, my_addrP, key)
    # release the lock after modifying the shared data
    key = False
    key = tell_unlock(map, my_addrP, key)
    lock_del.release()
    return result

@app.route("/election", methods=['POST'])
def election():
    global isLeader, leader_addrP, my_addrP, map, up_time
    try:
        resp = elect_leader(my_addrP, map, up_time)
        print("resp:", resp)
        leader_addrP = resp['leader']
        print("leader:", leader_addrP)
        if leader_addrP == my_addrP:
            isLeader = True
        else:
            isLeader = False

        return resp, 200
    except Exception as e:
        print("Error:", e)
        return {'error': 'An error occurred'}, 500
    # return elect_leader(my_addrP, map, up_time)


@app.route("/leader", methods=['POST'])
def leader():
    global leader_addrP, my_addrP, up_time, isLeader
    data = request.get_json()
    leader_addrP = data['leader']
    if leader_addrP == my_addrP:
        isLeader = True
    else:
        isLeader = False
    return {'message': 'done'}, 200

@app.route("/getnodeinfo", methods=['GET'])
def getnodeinfo():
    try:
        return {'leader': leader_addrP, 'isLeader': isLeader, 'up_time': up_time}, 200
    except Exception as e:
        print("Error:", e)
        return {'error': 'An error occurred'}, 500

@app.route("/lock", methods=['POST'])
def lock():
    r = request.get_json()
    if not key or lock_holder == r['requester']:
        return {'lockGranted': True}, 200
    else:
        return {'lockGranted': False}, 200

@app.route("/unlock", methods=['POST'])
def unlock():
    r = request.get_json()
    lock_holder = ""
    key = False
    return {"lock": "released"}, 200

@app.route("/setlock", methods=['POST'])
def setlock():
    r = request.get_json()
    key = r['setLockTo']
    return {"lock": "set"}, 200

if __name__ == "__main__":
    #webbrowser.open_new("http://127.0.0.1:5000/")
    app.run(host='0.0.0.0', port=5000)
