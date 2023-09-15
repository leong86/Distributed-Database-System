# this connects distributed system automatically

import requests

# these were the access points in GCP's cloud run
external_addrP = ['coen317api1-w4mi2pbvzq-uc.a.run.app',
                  'coen317api2-w4mi2pbvzq-uc.a.run.app',
                  'coen317api3-w4mi2pbvzq-uc.a.run.app',
                  'coen317api4-w4mi2pbvzq-uc.a.run.app',
                  'coen317api5-w4mi2pbvzq-uc.a.run.app',
                  'coen317api6-w4mi2pbvzq-uc.a.run.app', ]

addrPs = ['coen317api1-w4mi2pbvzq-uc.a.run.app',
          'coen317api2-w4mi2pbvzq-uc.a.run.app',
          'coen317api3-w4mi2pbvzq-uc.a.run.app',
          'coen317api4-w4mi2pbvzq-uc.a.run.app',
          'coen317api5-w4mi2pbvzq-uc.a.run.app',
          'coen317api6-w4mi2pbvzq-uc.a.run.app', ]
          
# these are the public IPs for a mysql instance in GCP
dbs = ['34.173.199.161',
        '34.66.207.154',
        '34.133.83.111',
        '35.223.137.65',
        '35.184.104.155',
        '104.154.104.207']

for i in range(0, len(addrPs)):
    if i == 0:
        requests.post("https://" + external_addrP[i] + '/join',
            json = {
                "my_addrP": addrPs[i],
                "db": dbs[i]
            })
    else:
        requests.post("https://" + external_addrP[i] + '/join',
            json = {
                "my_addrP": addrPs[i],
                "db": dbs[i],
                "addrP": addrPs[0],
            })

for i in range(0, len(addrPs)):
    requests.post("https://" + external_addrP[i] + '/save',
        json = {
            "id": i,
            "name": "string" + str(i)
        })
