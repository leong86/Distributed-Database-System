import requests
import pymysql
from random import randint
import threading

def save_rollback(nodes, node, data):
    """If saving an entry requires a rollback, we tell servers that commited to rollback by deleting item
    Message will be recieved if commited since it returns after commiting and closing the connection
    Messages wont be lost since we are using connection oriented comunication"""
    for saved_node in nodes:
        # execute reversal action until we reach the original node that provided an exception
        if node == saved_node:
            break
        else: # opposite of save is delete so we locally delete node that was able to commit
            response = requests.post('http://' + saved_node + '/localdelete',
                json = {
                "DeleteCondition": "id= '" + data['id'] + "'"
                })


def delete_rollback(map, node, data, deleted_data):
    """Same for save_rollback but we re-insert"""
    # select data that local envionment would have deleted
    # must send delete request to all known nodes, or until faulty node is reached
    for deleted_node in map[0]:
        # execute reversal action until we reach the original node that provided an exception
        if node == deleted_node:
            return # if we see node that failed, we can stop rollback
        else:
            for result in deleted_data: #loop again if deleted multiple lines
                response = requests.post('http://' + deleted_node + '/savesync',
                    json = {
                        "id": result[0], "name": result[1]
                    })
    for deleted_node in map[1]:
        # execute reversal action until we reach the original node that provided an exception
        if node == deleted_node:
            return # if we see node that failed, we can stop rollback
        else:
            for result in deleted_data: #loop again if deleted multiple lines
                response = requests.post('http://' + deleted_node + '/savesync',
                    json = {
                        "id": result[0], "name": result[1]
                    })

def select_local(db, data):
    """Selects data only on local database"""
    try:
        conn = pymysql.connect(host=db, user='root', password='root', database='test')
        cursor = conn.cursor()
        cursor.execute(data['query'])
        conn.commit()
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        # if executed properly, send data as a list
        return {'result': list(data)}, 200
    except:
        cursor.close()
        conn.close()
        return {'result:': "Error getting data"}, 400

def select_from_network(data, quarm_id, map, db):
    # first select from toher group
    response = None
    node_list = list(map[(quarm_id + 1) % 2])
    random_num = randint(0,len(node_list)-1)
    for n in node_list:
        node = node_list[random_num]
        try:
            response = requests.post('http://' + node + '/selectlocal', json = data)
            break;
        except:
            random_num  = (random_num + 1) % len(node_list)
    # then select from local db
    try:
        conn = pymysql.connect(host=db, user='root', password='root', database='test')
        cursor = conn.cursor()
        cursor.execute(data['query'])
        conn.commit()
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        # if all goes well, return merged result
        return {'result': list(data) + list(response.json()['result'])}, 200
    except:
        cursor.close()
        conn.close()
        return {"result": "error"}, 400

def saveto(db, data, quarm_id):
    """saves only to local table. Another node is responsible for managing the save"""
    if hash(data['id'])%2 != quarm_id: # data sent shouldn't be saved here anyways
        print("recieved inseret in error", hash(data['id'])%2, quarm_id)
        return {'saved': True}, 200
    try:
        conn = pymysql.connect(host=db, user='root', password='root', database='test')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO test_table (id, name) VALUES (%s, %s)", (data['id'], data['name']))
        conn.commit() # before this we ensure other nodes also committed data it needed to
        cursor.close()
        conn.close()
        return {'saved': True}, 200
    except:
        cursor.close()
        conn.close()
        return {'saved': False}, 400

def safe_save(db, map, data, quarm_id, my_addrP):
    """This function manages the safe save of an insert.
    It ensure the right tables get the right data.
    Additionally it ensures data is properly replicated"""
    print(hash(data['id'])%2, quarm_id)
    if hash(data['id'])%2 != quarm_id:
        #if we should not store this send to other group
        print("redirecting save")
        node_list = list(map[hash(data['id'])%2]) # gets all nodes that we should send insert request to
        # below, we choose a random node from the other group to send the request to
        r = requests.post('http://' + node_list[randint(0,len(node_list)-1)] + '/save', json = data)
        return r.json()
    try: # Enter this try is this group is responsible for this data
        conn = pymysql.connect(host=db, user='root', password='root', database='test')
        cursor = conn.cursor()
        for node in map[quarm_id]: # send save to all other nodes in group
            if node != my_addrP:
                r = requests.post('http://' + node + '/savesync', json = data)
                r_json = r.json()
                if not r_json['saved']: # if not saved
                    #execute rollback
                    # iterate through send saves and delete entries that were saved
                    save_rollback(map[quarm_id], node, data)

        cursor.execute("INSERT INTO test_table (id, name) VALUES (%s, %s)", (data['id'], data['name']))
        conn.commit() # before this we ensure other nodes also committed data it needed to
        cursor.close()
        conn.close()
        return {'saved': True}, 200
    except:
        cursor.close()
        conn.close()
        return {'saved': False}, 400

def share_map(map, s):
    """sends updated map to all known nodes"""
    for k in map[0]: # send update to all nodes
        requests.post('http://' + k + '/add', json = s)

    for k in map[1]:
        requests.post('http://' + k + '/add', json = s)

def local_delete(db, data, quarm_id, my_addrP):
    """Only deleted data on local database.
    External node is responsible for ensuring all data is properly deleted"""
    try:
        conn = pymysql.connect(host=db, user='root', password='root', database='test')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM test_table WHERE " + data['DeleteCondition'])
        conn.commit()
        cursor.close()
        conn.close()
        return {'result': True}, 200
    except:
        cursor.close()
        conn.close()
        return {'result': False}, 400

def safe_delete(db, map, data, quarm_id, my_addrP, key):
    """This node ensures all nodes needing to delete, is able to delete.
    Else, it will initiate a rollback. this will cover all/both groups"""
    # first get/backup data that we would have deleted in case of a rollback
    if key == True:
        deleted_data = select_from_network({"query": "SELECT * FROM test_table WHERE " + data["DeleteCondition"]}, quarm_id, map, db)[0]['result']
        try:
            conn = pymysql.connect(host=db, user='root', password='root', database='test')
            cursor = conn.cursor()
            for node_list in map: # send delete conditions to all known nodes
                for node in node_list:
                    if node != my_addrP:
                        r = requests.delete('http://' + node + '/localdelete', json = data)
                        r_json = r.json()
                        if not r_json['result']: # if not saved
                            delete_rollback(map, node, data, db, deleted_data)
                            cursor.close()
                            conn.close()
                            return {'saved': False}, 400


            cursor.execute("DELETE FROM test_table WHERE " + data['DeleteCondition'])
            conn.commit() # before this we ensure other nodes also committed data it needed to
            cursor.close()
            conn.close()
            return {'deleted': True}, 200
        except:
            delete_rollback(map, "", data, deleted_data) # if other error, rollback all
            cursor.close()
            conn.close()
            return {'deleted': False}, 400
    else:
        return {'deleted': False}, 408

def elect_leader(my_addrP, map, up_time):
    leader_addrP = my_addrP
    min_uptime = up_time
    # try:
    for node_list in map:
        for node in node_list:
            if node != my_addrP:
                r = requests.get('http://' + node + '/getnodeinfo')

                r_json = r.json()
                print("r_json:", r_json)
                if r_json['up_time'] < min_uptime:
                    min_uptime = r_json['up_time']
                    leader_addrP = node

    print("min_uptime:", min_uptime, " leader shouldf be", leader_addrP)

    # tell other nodes that this node is leader
    for node_list in map:
        for node in node_list:
            if node != my_addrP:
                requests.post('http://' + node + '/leader', json = {'leader': leader_addrP})
    print("leader is: ", leader_addrP)
    data = {'leader': leader_addrP, 'up_time': min_uptime}
    return data
        # return {'leader': leader_addrP, 'uptime': min_uptime}, {Status Code: 200}
    # except:
    #     data = {'leader': my_addrP, 'uptime': min_uptime}
    #     return data
        # return {'leader': my_addrP, 'uptime': min_uptime}, 200

def tell_lock(map, my_addrP, key):
    if key: # if we already have key, continue
        return True
    for node_list in map:
        for node in node_list:
            if node != my_addrP:
                resp = requests.post('http://' + node + '/lock', json = {'requester': my_addrP})
                resp = resp.json()
                if not resp['lockGranted']:
                    return False
    return True

def tell_unlock(map, my_addrP, key):
    for node_list in map:
        for node in node_list:
            if node != my_addrP:
                resp = requests.post('http://' + node + '/unlock', json = {'requester': my_addrP})
    return False
