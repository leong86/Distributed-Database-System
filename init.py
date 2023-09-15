# this connects distributed system automatically
import requests

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

for i in range(0, len(addrPs)):
    if i == 0:
        requests.post('http://' + external_addrP[i] + '/join',
            json = {
                "my_addrP": addrPs[i],
                "db": dbs[i]
            })
    else:
        requests.post('http://' + external_addrP[i] + '/join',
            json = {
                "my_addrP": addrPs[i],
                "db": dbs[i],
                "addrP": addrPs[0],
            })

for i in range(0, len(addrPs)):
    requests.post('http://' + external_addrP[i] + '/save',
        json = {
            "id": i,
            "name": "string" + str(i)
        })
