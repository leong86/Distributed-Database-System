import requests
import time
from random import randint
from threading import Thread


external_addrP = ['localhost:5000',
                    'localhost:5001',
                    'localhost:5002',
                    'localhost:5003',
                    'localhost:5004',
                    'localhost:5005', ]

addrPs = ['api1:5000',
            'api2:5000',
            'api3:5000',
            'api4:5000',
            'api5:5000',
            'api6:5000', ]

dbs = ['db1',
        'db2',
        'db3',
        'db4',
        'db5',
        'db6']

def save(addr, i):
    requests.post('http://' + addr + '/save',
        json = {
            "id": i,
            "name": 'string' + str(i)
        })

def select(addr, i):
    requests.post('http://' + addr + '/save',
        json = {
            "id": i,
            "name": 'string' + str(i)
        })

def delete(addr, i):
    requests.delete('http://' + addr + '/delete',
        json = {
            "DeleteCondition": "id='" + str(i) + "'"
        })

# insert 1000 values to one node
threads_single_insert = []
for i in range(7, 1007):
    threads_single_insert.append(Thread(target=save, args=[external_addrP[0], i]))

start_time = time.time()
for i in range(0, 1000):
    threads_single_insert[i].run()

print("--- %s seconds ---" % (time.time() - start_time))

#deleting test
start_time = time.time()
for i in range(7, 1007):
    delete(external_addrP[randint(0,5)], i)
print("--- %s seconds ---" % (time.time() - start_time))

# insert 1000 values to all nodes
threads_insert = []
for i in range(1007, 2007):
    threads_insert.append(Thread(target=save, args=[external_addrP[randint(0,5)], i]))

start_time = time.time()
for i in range(0, 1000):
    threads_insert[i].run()

print("--- %s seconds ---" % (time.time() - start_time))


# select 1000 times from one
threads_single_select = []
for i in range(0, 1000):
    threads_single_select.append(Thread(target=select, args=[external_addrP[0], i]))

start_time = time.time()
for i in range(0, 1000):
    threads_single_select[i].run()
print("--- %s seconds ---" % (time.time() - start_time))


# select 1000 times from all nodes
threads_select = []
for i in range(0, 1000):
    threads_select.append(Thread(target=select, args=[external_addrP[randint(0,5)], i]))

start_time = time.time()
for i in range(0, 1000):
    threads_select[i].run()
print("--- %s seconds ---" % (time.time() - start_time))
