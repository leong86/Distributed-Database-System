# COEN317python
Working python implementation

cd to the main folder and with docker installed and run this::

docker compose up --build

Once you see both the sql and python container running in docker, you can start using the web service
First run the init.py in the root directory to get everything linked, and populated, with some sample data
For the command, run "python3 init.py"

You can send a post request to localhost:5000/save
use the json format as follows:
{
    "id": <some int id>,
    "name": <some string like: "Hello!">
}

Select by:
localhost/select
with json data as:
{
    "query": "SELECT * FROM test_table"
}

Delete by:
localhost:5003/delete
with json data as:
{
    "DeleteCondition": "id='1' or id='4'"
}

With all containers running, a request can be send to any port between, and including, 5000 and 5005

Links to some requests to connect nodes together. just setting up distributed system for future communication.

You can run init.py to connect all the nodes so they can start servicing requests. This also has the request form for connecting the distributed database if you want to add more nodes into the system.

A json file is provided with most of the requests. A few internal requests where left out for simplicity.

To deploy in a cloud envionment. Set up sql instances and save their public ip, create a cloud instance for each api. Use the init.py in the gcp folder with changed addresses and database addresses. In the .py alls ensure they use https for all requests. 
