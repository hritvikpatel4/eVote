# ---------------------------------------- IMPORT HERE ----------------------------------------

from flask import Flask, jsonify, make_response, request
import docker, json, logging, os, re, requests, subprocess, threading, time

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode()

current_orderer_name = node_name

orderer = Flask(__name__)
host = "0.0.0.0"
port = os.environ["CUSTOM_PORT"]
lower_level_port = 80
orderer_port = 80
bc_port = 80

ORDERER_LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)

logging.basicConfig(filename=ORDERER_LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

receiver_q = []                 # This Q contains batch from BC to orderer
temp_q = []                     # This Q contains the batches which were sent by the BC during the batching logic
extra_batch_q = []              # This Q contains the extra batches which are not in the internsection_batch
batched_batchvotes = []         # This is a structure which stores the vote data. IT'S A LIST(LIST(DICT)) eventually
orderer_sets_received = 0       # This is a counter to check whether we have received all the batches from other orderers on the network
number_of_orderers = 3          # total number of orderers in each hierarchy
orderer_number = 0              # the current orderer number which is running
unique_votes = {}               # This is a structure which is used for detecting duplicate batches

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

# Convert set(str) to list(dict)
def deTransformBatch(data):
    temp = []

    for i in range(len(data)):
        temp.append(json.loads(data[i]))
    
    return temp

# Convert list(list(dict)) to list(list(str))
def transformBatch(data):
    temp = []

    for i in range(len(data)):
        temp2 = []
        
        for j in range(len(data[i])):
            temp2.append(json.dumps(data[i][j]))
        
        temp.append(temp2)
    
    return temp

def getNumberOfOrderers():
    counter = 0
    client = docker.from_env()
    container_list = client.containers.list()

    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name):
            counter += 1
    
    client.close()
    return counter

def getOrdererIPs():
    """
    return -> list of ip addr
    """
    client = docker.from_env()
    container_list = client.containers.list()

    # ip_list contains ip addresses of all orderers
    orderer_ip_list = []
    
    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name) and container.name != current_orderer_name:
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            orderer_ip_list.append(out.output.decode().split("\n")[0])
    
    client.close()
    return orderer_ip_list

def getBCIPs():
    """
    return -> list of ip addr
    """
    client = docker.from_env()
    container_list = client.containers.list()

    # ip_list contains ip addresses of all orderers
    bc_ip_list = []
    
    for container in container_list:
        if re.search("^bc[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            bc_ip_list.append(out.output.decode().split("\n")[0])
    
    client.close()
    return bc_ip_list

def send_batch_votes():
    data = {
        "batch_data": receiver_q
    }

    orderer_ip_list = getOrdererIPs()

    logging.debug("Starting broadcast to peer orderers with the receiver_q")

    for ip in orderer_ip_list:
        res = requests.post("http://" + ip + ":" + str(orderer_port) + "/api/orderer/receiveBatchesFromPeerOrderer", json=data)

        if res.status_code != 200:
            logging.error("Failed to send receiver_q to peer orderer with IP = {}".format(ip))
    
    logging.debug("Sent batch to all peer orderers")

def intersect_batches():
    if len(batched_batchvotes) > 0:
        logging.debug("Starting intersection")
        transformed_batched_batchvotes = transformBatch(batched_batchvotes)
        ans = set(transformed_batched_batchvotes[0])

        for batch in transformed_batched_batchvotes:
            ans = ans.intersection(batch)
        
        extra_batch = receiver_q.difference(ans)

        ans = deTransformBatch(list(ans))
        
        for data in list(extra_batch):
            extra_batch_q.append(data)

        ans = sorted(ans, key=lambda x: x["batch_id"])
        logging.debug("Intersection batch {}".format(ans))
        return ans

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@orderer.route("/api/orderer/receiveFromBCNode", methods=["POST"])
# Receive vote from LBC node and broadcast to peer orderers
def receiveFromBCNode():
    """
        params = {
            string: int
            
            "candidate_id_1": num_votes,
            "candidate_id_2": num_votes,
            "candidate_id_3": num_votes,
            "batch_id": unique_int
            ...
        }
    """
    params = request.get_json()

    # logging.info("Params {} received from BC with IP = {}".format(params, request.remote_addr))

    # add the vote into the queue
    receiver_q.append(params)

    # ip_list contains ip addresses of all orderers
    orderer_ip_list = getOrdererIPs()
    
    # logging.debug("Now broadcasting to peer orderers")

    # broadcast vote to all peer orderers by calling their receiveVoteFromOrderer APIs
    for ip in orderer_ip_list:
        res = requests.post("http://" + ip + ":80" + "/api/orderer/receiveBatchFromPeerOrderer", json=params)

        if res.status_code != 200:
            logging.error("could not forward to peer orderer with IP = {}".format(ip))
    
    # logging.debug("Broadcast Finished")

    return make_response("Added to orderer receiver_q", 200)

@orderer.route("/api/orderer/receiveBatchFromPeerOrderer", methods=["POST"])
# Receives batch from peer orderers.
# The vote comes from a peer orderer that itself received from a LBC node
def receiveVoteFromOrderer():
    """
        params = {
            string: int
            
            "candidate_id_1": num_votes,
            "candidate_id_2": num_votes,
            "candidate_id_3": num_votes,
            "batch_id": unique_int
            ...
        }
    """
    params = request.get_json()
    # logging.debug("Received vote data from peer orderer {}".format(params))

    # Detect duplicate votes
    if params["batch_id"] not in unique_votes:
        receiver_q.append(params)
        unique_votes[params["batch_id"]] = True

        return make_response("Added to orderer receiver_q", 200)

    return make_response("Duplicate batch received", 400)

@orderer.route("/api/orderer/startBatching", methods=["GET"])
# Receives the signal from load balancer to send batch
def startBatching():
    logging.info("Running send_batch_votes()")
    send_batch_votes()

    return make_response("Received signal to start batching", 200)

@orderer.route("/api/orderer/receiveBatchesFromPeerOrderer", methods=["POST"])
# Before calculating intersection, this API collects batches from every peer orderer
def receiveBatchesFromPeerOrderer():
    global orderer_sets_received
    global batched_batchvotes
    
    orderer_sets_received += 1
    
    batch_data_received = request.get_json()["batch_data"]
    batched_batchvotes.append(batch_data_received)

    logging.debug("Received batch from an orderer with params {}".format(batch_data_received))

    number_of_orderers = getNumberOfOrderers()

    # This executes only when all batches from peers have been received
    if orderer_sets_received == number_of_orderers - 1:
        intersection_batch = intersect_batches()
        
        orderer_sets_received = 0
        batched_batchvotes = []
    
    return make_response("Done calculating intersection batch", 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
    orderer_name = process_output.stdout.decode()
    orderer_number = orderer_name[len("orderer"):]
    
    # logging.info("Timer started!")
    # init_timer()

    orderer.run(debug=True, port=port, host=host, use_reloader=False)
