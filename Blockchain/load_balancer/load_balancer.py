# ---------------------------------------- IMPORT HERE ----------------------------------------

from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from queue import Queue
import docker, logging, os, random, re, requests, subprocess, threading

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode()

timer = None
app = Flask(__name__)
host = "0.0.0.0"
port = os.environ["CUSTOM_PORT"]
LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
next_timeout = None
HOLD_VOTES_TEMPORARY = False
temp_q = Queue(maxsize=0)

logging.basicConfig(filename=LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

def emptyTempQueue():
    while not temp_q.empty():
        vote = temp_q.get()

        requests.post("http://localhost:80/castvote", json=vote)

# Timer function
def timerfunc():
    global next_timeout

    while True:
        while datetime.now() != next_timeout:
            pass

        logging.debug("Timeout! Updating the number of orderers and executing batching of votes")

        # Put extra votes into another temp queue
        HOLD_VOTES_TEMPORARY = True
        
        # Call API on the orderers to execute batching
        client = docker.from_env()
        container_list = client.containers.list()
        ip_list = []
        
        for container in container_list:
            if re.search("^orderer[1-9][0-9]*", container.name):
                out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
                ip_list.append(out.output.decode().split("\n")[0])
        
        logging.debug("Calling batching API on peer orderers")

        for ip in ip_list:
            requests.get("http://" + ip + "/api/orderer/startbatching")
        
        logging.debug("Finished calling batching API on peer orderers")

        # Wait till we receive ack from random orderer. GOTO /receiveack

# Init timer
def init_timer():
    global timer

    if not timer:
        timer = threading.Thread(target = timerfunc)
        timer.start()

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@app.route("/api/lb/receiveack", methods=["GET"])
# Receives ack from random orderer that intersection is done and now send the temp votes back
def receiveAck():
    HOLD_VOTES_TEMPORARY = False

    emptyTempQueue()
    next_timeout = datetime.now() + timedelta(seconds=30)

@app.route('/castvote', methods=['POST'])
# forwards vote from webserver to lbc
def castVote():
    # Check if we should put data into temp_q
    if HOLD_VOTES_TEMPORARY:
        temp_q.put(request.get_json())
    
    else:
        client = docker.from_env()
        clist = client.containers.list()

        ip_list = []

        for container in clist:
            if re.search("^lbc[1-9][0-9]*", container.name):
                out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
                ip_list.append(out.output.decode().split("\n")[0])

        if(len(ip_list) == 0):
            return jsonify({"status": "No LBC containers running"}, 400)

        rand_lbc_ip = random.choice(ip_list)
        print("ip list = ", ip_list)

        params = request.get_json()

        requests.post("http://" + rand_lbc_ip + ":80" + "/api/lbc/receivevote", json=params)
        print("rand lbc ip = ", rand_lbc_ip)
        print()

    return make_response("", 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    next_timeout = datetime.now() + timedelta(seconds=30)
    init_timer()
    
    app.run(debug=True, host=host, port=port, use_reloader=False)
