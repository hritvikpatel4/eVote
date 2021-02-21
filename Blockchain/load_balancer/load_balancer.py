# ---------------------------------------- IMPORT HERE ----------------------------------------

from datetime import datetime, timedelta
from flask import Flask, make_response, jsonify, request
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
bc_port = 80
LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
next_timeout = None
HOLD_VOTES_TEMPORARY = False
temp_q = Queue(maxsize=0)

logging.basicConfig(filename=LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

def getBCIPs():
    """
    returns list of ip addr
    """

    client = docker.from_env()
    container_list = client.containers.list()

    bc_ip_list = []

    for container in container_list:
        if re.search("^bc[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            bc_ip_list.append(out.output.decode().split("\n")[0])
        
    return bc_ip_list

def emptyTempQueue():
    while not temp_q.empty():
        vote = temp_q.get()

        res = requests.post("http://localhost:80/castvote", json=vote)
        
        if res.status_code == 200:
            continue
        else:
            logging.debug("Failed to send this vote {}".format(vote))

# Timer function
def timerfunc():
    global next_timeout

    while True:
        while datetime.now().strftime("%s") != next_timeout:
            pass

        logging.debug("Timeout! Updating the number of orderers and executing batching of votes")
        logging.debug("Timeout next_timeout: {}".format(next_timeout))

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

####### IDEA to kill old thread and start new thread

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

    logging.debug("emptying temp queue")
    emptyTempQueue()
    logging.debug("emptied temp queue")
    next_timeout = (datetime.now() + timedelta(seconds=60)).strftime("%s")
    logging.debug("receiveack next_timeout: {}".format(next_timeout))

    return make_response("", 200)

@app.route("/api/test", methods=["POST"])
# Test API
def testAPI():
    params = request.get_json()
    batch1 = {
        "get_batch": [{"vote_id": 10, "candidate_id": 20}, {"vote_id": 20, "candidate_id": 30}]
    }
    batch2 = {
        "get_batch": [{"vote_id": 11, "candidate_id": 21}, {"vote_id": 21, "candidate_id": 31}]
    }

    client = docker.from_env()
    container_list = client.containers.list()

    ip_list = []
    
    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            ip_list.append(out.output.decode().split("\n")[0])

    for ip in ip_list:
        requests.post("http://" + ip + ":80" + "/api/orderer/receivebatch", json=batch1)
        requests.post("http://" + ip + ":80" + "/api/orderer/receivebatch", json=batch2)
    
    return make_response("Done testing receivebatch", 200)

@app.route("/toy", methods=["POST"])
def toy():
    params = request.get_json()
    
    bc_ip_list = getBCIPs()
    rand_lbc_ip = random.choice(bc_ip_list)

    requests.post("http://" + rand_lbc_ip + str(bc_port) + "/api/bc/receiveVoteFromLowerLevel", json=params)

    return make_response("Success!", 200)

@app.route('/castvote', methods=['POST'])
# forwards vote from webserver to lbc
def castVote():
    # Check if we should put data into temp_q
    if HOLD_VOTES_TEMPORARY:
        params = request.get_json()
        vote_id_type = isinstance(params["vote_id"], int)
        candidate_id_type = isinstance(params["candidate_id"], int)
        
        if vote_id_type and candidate_id_type:
            logging.debug("Pushing requests temporarily to another queue")
            temp_q.put(request.get_json())
        
        else:
            return make_response("", 400)
    
    else:
        client = docker.from_env()
        clist = client.containers.list()

        ip_list = []

        for container in clist:
            if re.search("^bc[1-9][0-9]*", container.name):
                out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
                ip_list.append(out.output.decode().split("\n")[0])

        if(len(ip_list) == 0):
            return jsonify({"status": "No LBC containers running"}, 400)

        rand_lbc_ip = random.choice(ip_list)
        print("ip list = ", ip_list)

        params = request.get_json()
        vote_id_type = isinstance(params["vote_id"], int)
        candidate_id_type = isinstance(params["candidate_id"], int)
        
        if vote_id_type and candidate_id_type:
            requests.post("http://" + rand_lbc_ip + ":80" + "/api/lbc/receivevote", json=params)
            print("rand lbc ip = ", rand_lbc_ip)
            print()
        
        else:
            return make_response("", 400)

    return make_response("", 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    next_timeout = (datetime.now() + timedelta(seconds=60)).strftime("%s")
    logging.debug("INIT next_timeout: {}".format(next_timeout))
    init_timer()
    
    app.run(debug=True, host=host, port=port, use_reloader=False)
