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
lb_port = 8080
ORDERER_LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
PUT_IN_TIMEOUT_Q = False

logging.basicConfig(filename=ORDERER_LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

receiver_q = []                 # This Q contains batch from BC to orderer
during_timeout_q = []           # This Q contains the batches which were sent by the BC during the batching logic
diff_batch_q = []               # This Q contains the extra batches which are not in the internsection_batch
batched_batchvotes = []         # This is a structure which stores the vote data. IT'S A LIST(LIST(DICT)) eventually
number_of_orderers = 3          # total number of orderers in each hierarchy
orderer_number = 0              # the current orderer number which is running
unique_votes = {}               # This is a structure which is used for detecting duplicate batches

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

# Convert set(str) to list(dict)
# def deTransformBatch(data):
#     temp = []

#     for i in range(len(data)):
#         temp.append(json.loads(data[i]))
    
#     return temp

# Convert list(list(dict)) to list(list(str))
# def transformBatch(data):
#     temp = []

#     for i in range(len(data)):
#         temp2 = []
        
#         for j in range(len(data[i])):
#             temp2.append(json.dumps(data[i][j]))
        
#         temp.append(temp2)
    
#     return temp

# [[{1:1}, {2:1}, {3:1}], [{1:1}, {2:1}, {3:1}], [{1:1}, {2:1}, {3:1}]]
# [[1, 2, 3], [1, 2, 3], [1, 2, 3]]

# Convert list(list(dict)) to list(list(int))
def extractBatchIDs(data, dictmapping):
    l1 = []

    for i in range(len(data)):
        l2 = []

        for j in range(len(data[i])):
            current_id = data[i][j]["batch_id"]
            dictmapping[str(current_id)] = data[i][j]
            
            l2.append(data[i][j]["batch_id"])
        
        l1.append(l2)
    
    return l1, dictmapping

# Convert list(dict) to list(int)
def transformRecQ(data):
    temp = []

    for i in range(len(data)):
        temp.append(data[i]["batch_id"])
    
    return temp

# Convert list(int) to list(dict) by using the dict mapping
def buildBatchFromMapping(data, batchid_batch_mapping):
    temp = []

    for i in range(len(data)):
        temp.append(batchid_batch_mapping[str(data[i])])

    return temp

def getOnlyBatchIDs(listdata):
    batch_ids = []

    for data in listdata:
        batch_ids.append(data["batch_id"])
    
    return batch_ids

def getOrdererIPs():
    """
    return -> list of ip addr
    """

    client = docker.from_env()
    container_list = client.containers.list()
    
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

    bc_ip_list = []
    
    for container in container_list:
        if re.search("^bc[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            bc_ip_list.append(out.output.decode().split("\n")[0])
    
    client.close()
    return bc_ip_list

def getLBIPs():
    """
    return -> list of ip addr
    """

    client = docker.from_env()
    container_list = client.containers.list()

    lb_ip_list = []
    
    for container in container_list:
        if re.search("^load_balancer[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            lb_ip_list.append(out.output.decode().split("\n")[0])
    
    client.close()
    return lb_ip_list

def getNumberOfOrderers():
    counter = 0
    client = docker.from_env()
    container_list = client.containers.list()

    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name):
            counter += 1
    
    client.close()
    return counter

def flushTimeoutQ():
    """
    Forwards all the batches to PEER ORDERERS present in the during_timeout_q.
    The batches enter that queue when we are basically executing intersection logic and have received
    timeout from the load balancer
    """
    
    orderer_ip_list = getOrdererIPs()

    for batch in during_timeout_q:
        for ip in orderer_ip_list:
            # data = json.loads(batch)
            res = requests.post("http://" + ip + ":" + str(orderer_port) + "/api/orderer/receiveBatchFromPeerOrderer", json=batch)

            if res.status_code != 200:
                logging.error("Error sending batch to orderer with IP = {}".format(ip))
    
    during_timeout_q.clear()

def flushDiffQ():
    """
    Forwards the batches from this queue to PEER ORDERERS.
    Batches enter this queue from the output of the difference between receiver_q and the intersection batch
    """

    orderer_ip_list = getOrdererIPs()
    
    for batch in diff_batch_q:
        for ip in orderer_ip_list:
            # data = json.loads(batch)
            res = requests.post("http://" + ip + ":" + str(orderer_port) + "/api/orderer/receiveBatchFromPeerOrderer", json=batch)

            if res.status_code != 200:
                logging.error("Error sending batch to orderer with IP = {}".format(ip))

    diff_batch_q.clear()

def emptyReceiverQ():
    """
    Empties the receiver_q
    """
    
    receiver_q.clear()

def send_batch_votes():
    global batched_batchvotes

    batchids_rec = getOnlyBatchIDs(receiver_q)
    batchids_timeout = getOnlyBatchIDs(during_timeout_q)
    batchids_diff = getOnlyBatchIDs(diff_batch_q)
    
    logging.debug("----------------------------------------------------------------")
    logging.debug("Receiver_Q {}".format(batchids_rec))
    logging.debug("----------------------------------------------------------------")
    logging.debug("Timeout_Q {}".format(batchids_timeout))
    logging.debug("----------------------------------------------------------------")
    logging.debug("Diff_Q {}".format(batchids_diff))
    logging.debug("----------------------------------------------------------------")

    orderer_ip_list = getOrdererIPs()

    # logging.debug("Starting broadcast to peer orderers with the receiver_q")

    batched_batchvotes.append(receiver_q)

    for ip in orderer_ip_list:
        data = {
            "batch_data": receiver_q
        }
        
        batchids_sent = getOnlyBatchIDs(data["batch_data"])

        logging.debug("----------------------------------------------------------------")
        logging.debug("Data sent {} to orderer{}".format(batchids_sent, getOrdererNumber(ip)))
        logging.debug("----------------------------------------------------------------")
        
        res = requests.post("http://" + ip + ":" + str(orderer_port) + "/api/orderer/receiveBatchesFromPeerOrderer", json=data)

        if res.status_code != 200:
            logging.error("Failed to send receiver_q to peer orderer with IP = {}".format(ip))
    
    # logging.debug("Sent batch to all peer orderers")

def intersect_batches():
    global diff_batch_q

    if len(batched_batchvotes) > 0:
        logging.debug("Starting intersection")

        batchid_batch_mapping = {}
        
        # extracted_batched_batchvotes = list(list(int)) where int is the batch_id
        extracted_batched_batchvotes, batchid_batch_mapping = extractBatchIDs(batched_batchvotes, batchid_batch_mapping)

        ans = set(extracted_batched_batchvotes[0])
        print("Batch taken for intersection {}".format(extracted_batched_batchvotes[0]))

        for i in range(1, len(extracted_batched_batchvotes)):
            print("Batch taken for intersection {}".format(extracted_batched_batchvotes[i]))
            # print("Batch taken for intersection {}".format(batch))

            ans = ans.intersection(set(extracted_batched_batchvotes[i]))
        
        transformed_rev_q = set(transformRecQ(receiver_q))
        diff_batch = transformed_rev_q.difference(ans)

        result = buildBatchFromMapping(list(ans), batchid_batch_mapping)

        diff_batch_q = buildBatchFromMapping(list(diff_batch), batchid_batch_mapping)

        result = sorted(result, key=lambda x: x["batch_id"])

        batch_ids = getOnlyBatchIDs(result)

        print("Intersection batch {}".format(batch_ids))
        logging.debug("----------------------------------------------------------------")
        logging.debug("Intersection batch {}".format(batch_ids))
        logging.debug("----------------------------------------------------------------")

        batchid_batch_mapping.clear()

        return result

def getOrdererNumber(ip):
    return int(ip.split(".")[-1]) - 4

def getBCNumber(ip):
    return int(ip.split(".")[-1]) - 1

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

    global unique_votes
    
    if PUT_IN_TIMEOUT_Q:
        params = request.get_json()

        during_timeout_q.append(params)
    
    else:
        params = request.get_json()

        if str(params["batch_id"]) not in unique_votes:
            print("batchid = {} from bc{}".format(params["batch_id"], getBCNumber(request.remote_addr)))
        
            logging.debug("----------------------------------------------------------------")
            logging.debug("batchid = {} from bc{}".format(params["batch_id"], getBCNumber(request.remote_addr)))
            logging.debug("----------------------------------------------------------------")

            receiver_q.append(params)
            unique_votes[str(params["batch_id"])] = True

            orderer_ip_list = getOrdererIPs()

            for ip in orderer_ip_list:
                res = requests.post("http://" + ip + ":80" + "/api/orderer/receiveBatchFromPeerOrderer", json=params)

                if res.status_code != 200:
                    logging.error("could not forward to peer orderer with IP = {}".format(ip))

            return make_response("Added to orderer receiver_q", 200)
    
        logging.debug("----------------------------------------------------------------")
        logging.debug("Duplicate batch received from bc{}".format(getBCNumber(request.remote_addr)))
        logging.debug("----------------------------------------------------------------")
        
        return make_response("Duplicate batch received", 200)

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
    
    global unique_votes

    params = request.get_json()
    # logging.debug("Received vote data from peer orderer {}".format(params))
    # print("batchid = {} from IP = {}".format(params["batch_id"], request.remote_addr))

    # Detect duplicate votes
    if str(params["batch_id"]) not in unique_votes:
        print("batchid = {} from orderer{}".format(params["batch_id"], getOrdererNumber(request.remote_addr)))
        
        logging.debug("----------------------------------------------------------------")
        logging.debug("batchid = {} from orderer{}".format(params["batch_id"], getOrdererNumber(request.remote_addr)))
        logging.debug("----------------------------------------------------------------")
        
        receiver_q.append(params)
        unique_votes[str(params["batch_id"])] = True

        return make_response("Added to orderer receiver_q", 200)
    
    logging.debug("----------------------------------------------------------------")
    logging.debug("Duplicate batch received from orderer{}".format(getOrdererNumber(request.remote_addr)))
    logging.debug("----------------------------------------------------------------")
    return make_response("Duplicate batch received", 200)

@orderer.route("/api/orderer/startBatching", methods=["GET"])
# Receives the signal from load balancer to send batch
def startBatching():
    global PUT_IN_TIMEOUT_Q
    PUT_IN_TIMEOUT_Q = True
    
    # logging.info("Running send_batch_votes()")
    send_batch_votes()

    return make_response("Received signal to start batching", 200)

@orderer.route("/api/orderer/receiveBatchesFromPeerOrderer", methods=["POST"])
# Before calculating intersection, this API collects batches from every peer orderer
def receiveBatchesFromPeerOrderer():
    global batched_batchvotes
    global PUT_IN_TIMEOUT_Q
    
    batch_data_received = request.get_json()["batch_data"]
    batched_batchvotes.append(batch_data_received)

    # logging.debug("Received batch from an orderer with params {}".format(batch_data_received))

    batchids = getOnlyBatchIDs(batch_data_received)
    
    logging.debug("----------------------------------------------------------------")
    logging.debug("Received batch of batches from orderer{} with batch_ids {}".format(getOrdererNumber(request.remote_addr), batchids))
    logging.debug("----------------------------------------------------------------")

    number_of_orderers = getNumberOfOrderers()

    # This executes only when all batches from peers have been received
    if len(batched_batchvotes) == number_of_orderers:
        batchids_rec = getOnlyBatchIDs(receiver_q)
        batchids_timeout = getOnlyBatchIDs(during_timeout_q)
        batchids_diff = getOnlyBatchIDs(diff_batch_q)
        
        logging.debug("----------------------------------------------------------------")
        logging.debug("Receiver_Q {}".format(batchids_rec))
        logging.debug("----------------------------------------------------------------")
        logging.debug("Timeout_Q {}".format(batchids_timeout))
        logging.debug("----------------------------------------------------------------")
        logging.debug("Diff_Q {}".format(batchids_diff))
        logging.debug("----------------------------------------------------------------")
        
        intersection_batch = intersect_batches()

        # Find which random orderer will broadcast
        rand_ord_num = 0
        for vote in intersection_batch:
            rand_ord_num += (vote["batch_id"])
        
        rand_ord_num = (rand_ord_num % number_of_orderers) + 1

        logging.debug("Random orderer{} will broadcast".format(rand_ord_num))

        if rand_ord_num == int(orderer_number):
            data = {
                "final_batch": intersection_batch
            }

            bc_ip_list = getBCIPs()

            logging.debug("I will broadcast to lower level. My orderer number is {}".format(rand_ord_num))

            for ip in bc_ip_list:
                res = requests.post("http://" + ip + ":" + str(bc_port) + "/api/bc/writeToBlockchain", json=data)

                if res.status_code != 200:
                    logging.error("Error broadcasting to lower level with IP = {}".format(ip))
            
            logging.debug("Broadcast finished to lower level")

            lb_ip_list = getLBIPs()

            for ip in lb_ip_list:
                res = requests.get("http://" + ip + ":" + str(lb_port) + "/api/lb/receiveAck")

                if res.status_code != 200:
                    logging.error("Error sending ACK to LB with IP = {}".format(ip))
        
        batched_batchvotes.clear()

        emptyReceiverQ()
        flushTimeoutQ()
        flushDiffQ()

        PUT_IN_TIMEOUT_Q = False
    
    return make_response("Done calculating intersection batch", 200)

###### figure whats wrong with orderer1 not sending the intersection batch for 5 votes
###### Write to csv with correct hashes
###### Encrypt CSV
###### Work on forwarding data to HBC
###### RSA auth

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
    orderer_name = process_output.stdout.decode()
    orderer_number = orderer_name[len("orderer"):]

    orderer.run(debug=True, port=port, host=host, use_reloader=False)
