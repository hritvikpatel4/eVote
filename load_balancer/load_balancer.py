# ---------------------------------------- IMPORT HERE ----------------------------------------

# from custom_timer import RepeatedTimer
from flask import Flask, make_response, jsonify, request
from queue import Queue
import docker, logging, os, random, re, requests, subprocess, threading

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode().strip("\n")

# timer = None
load_balancer = Flask(__name__)
host = "0.0.0.0"
# port = os.environ["CUSTOM_PORT"]
bc_port = 80
orderer_port = 80
LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
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
    
    client.close()
    return bc_ip_list

def getOrdererIPs():
    """
    returns list of ip addr
    """

    client = docker.from_env()
    container_list = client.containers.list()

    orderer_ip_list = []

    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            orderer_ip_list.append(out.output.decode().split("\n")[0])
        
    client.close()
    return orderer_ip_list

def emptyTempQueue():
    while not temp_q.empty():
        vote = temp_q.get()

        res = requests.post("http://" + node_ip + ":80" + "/castVote", json=vote)
        
        if res.status_code == 200:
            continue
        else:
            logging.debug("Failed to send this vote {}".format(vote))

def callOrdererBatching():
    global HOLD_VOTES_TEMPORARY
    # timer.pause()

    # Put extra votes into another temp queue
    HOLD_VOTES_TEMPORARY = True
    
    orderer_ip_list = getOrdererIPs()

    for ip in orderer_ip_list:
        requests.get("http://" + ip + ":" + str(orderer_port) + "/api/orderer/startBatching")
    
    logging.debug("Finished calling batching API on peer orderers")

    # Wait till we receive ack from random orderer. GOTO /receiveack
    return

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@load_balancer.route("/health")
# API to handle health requests from google
def health():
    return make_response("Alive and running!", 200)

@load_balancer.route("/api/lb/triggerBatching", methods=["GET"])
# API which calls the callOrdererBatching
def triggerBatching():
    callOrdererBatching()

    return make_response("", 200)

@load_balancer.route("/api/lb/receiveAck", methods=["GET"])
# Receives ack from random orderer that intersection is done and now send the temp votes back
def receiveAck():
    global HOLD_VOTES_TEMPORARY
    HOLD_VOTES_TEMPORARY = False

    logging.debug("emptying temp queue")
    empty_temp_queue_thread = threading.Thread(target=emptyTempQueue)
    empty_temp_queue_thread.start()
    logging.debug("emptied temp queue")
    
    res = requests.get("http://0.0.0.0:8080" + "/resumeTimer")
    if res.status_code != 200:
        logging.error("Could not resume timer")
        print("could not resume timer")
    
    # timer.start()

    return make_response("", 200)

@load_balancer.route('/castVote', methods=['POST'])
# forwards vote from webserver to lbc
def castVote():
    # Check if we should put data into temp_q
    if HOLD_VOTES_TEMPORARY:
        params = request.get_json()
        
        for data in params:
            if isinstance(params[data], int) == False:
                return make_response("Invalid data sent!", 400)
        
        logging.debug("Pushing requests temporarily to another queue")
        temp_q.put(params)
    
    else:
        bc_ip_list = getBCIPs()

        rand_bc_ip = random.choice(bc_ip_list)
        print("bc ip list = ", bc_ip_list)

        params = request.get_json()
        
        for data in params:
            if isinstance(params[data], int) == False:
                return make_response("Invalid data sent!", 400)
        
        print(params)
        
        requests.post("http://" + rand_bc_ip + ":" + str(bc_port) + "/api/bc/receiveVoteFromLowLevel", json=params)
        print("rand bc ip = ", rand_bc_ip)
        print()

    return make_response("Sent vote to BC", 200)

@load_balancer.route('/getElectionResult', methods=["GET"])
# returns the election result back to the client
def getElectionResult():
    bc_ip_list = getBCIPs()
    rand_bc_ip = random.choice(bc_ip_list)

    res = requests.get("http://" + rand_bc_ip + ":" + str(bc_port) + "/api/bc/calculateElectionResult")

    result = res.json()
    
    return make_response(result, 200)

# ---------------------------------------- MAIN ----------------------------------------

def main():
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))
    # print("timer started")
    # timer = RepeatedTimer(60, callOrdererBatching)
    # timer.start()
    
    return load_balancer

if __name__ == '__main__':
    main()

application = main()
