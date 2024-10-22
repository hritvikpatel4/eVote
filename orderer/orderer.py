# ---------------------------------------- IMPORT HERE ----------------------------------------

from flask import Flask, jsonify, make_response, request
import docker, json, logging, os, re, requests, subprocess, threading, time

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode().strip("\n")

current_orderer_name = node_name

orderer_number = int(node_name[len("orderer"):])              # the current orderer number which is running

orderer = Flask(__name__)
host = "0.0.0.0"
lower_level_port = 80
orderer_port = 80
bc_port = 80
lb_port = 80
ORDERER_LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
PUT_IN_TIMEOUT_Q = False

logging.basicConfig(filename=ORDERER_LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

receiver_q = []                 # This Q contains batch from BC to orderer
during_timeout_q = []           # This Q contains the batches which were sent by the BC during the batching logic
diff_batch_q = []               # This Q contains the extra batches which are not in the intersection_batch
batched_batchvotes = []         # This is a structure which stores the vote data. IT'S A LIST(LIST(DICT)) eventually
number_of_orderers = 3          # total number of orderers in each hierarchy
unique_votes = {}               # This is a structure which is used for detecting duplicate batches

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

# [[{1:1}, {2:1}, {3:1}], [{1:1}, {2:1}, {3:1}], [{1:1}, {2:1}, {3:1}]]
# [[1, 2, 3], [1, 2, 3], [1, 2, 3]]

# Convert list(list(dict)) to list(list(tuple(int)))
def extractAllIDs(data, dictmapping):
    l1 = []

    for i in range(len(data)):
        l2 = []

        for j in range(len(data[i])):
            current_level = data[i][j]["level_number"]
            current_clusterid = data[i][j]["cluster_id"]
            current_batchid = data[i][j]["batch_id"]
            
            temp_tuple = (current_level, current_clusterid, current_batchid)
            dictmapping[temp_tuple] = data[i][j]
            
            l2.append(temp_tuple)
        
        l1.append(l2)
    
    return l1, dictmapping

# Convert list(dict) to list(tuple(int))
def transformRecQ(data):
    temp = []

    for i in range(len(data)):
        current_level = data[i]["level_number"]
        current_clusterid = data[i]["cluster_id"]
        current_batchid = data[i]["batch_id"]

        temp_tuple = (current_level, current_clusterid, current_batchid)
        temp.append(temp_tuple)
    
    return temp

# Convert list(tuple(int)) to list(dict) by using the dict mapping
def buildBatchFromMapping(data, id_batch_mapping):
    temp = []

    for i in range(len(data)):
        temp.append(id_batch_mapping[data[i]])

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

def getNumberOfBC():
    counter = 0
    client = docker.from_env()
    container_list = client.containers.list()

    for container in container_list:
        if re.search("^bc[1-9][0-9]*", container.name):
            counter += 1
    
    client.close()
    return counter

def flushTimeoutQ():
    """
    Forwards all the batches to PEER ORDERERS present in the during_timeout_q and adds it to its own rec_q.
    The batches enter that queue when we are basically executing intersection logic and have received
    timeout from the load balancer
    """
    global unique_votes

    batchids_timeout = getOnlyBatchIDs(during_timeout_q)
    
    orderer_ip_list = getOrdererIPs()

    for batch in during_timeout_q:
        for ip in orderer_ip_list:
            res = requests.post("http://" + ip + ":" + str(orderer_port) + "/api/orderer/receiveBatchFromPeerOrderer", json=batch)

            if res.status_code != 200:
                logging.error("Error sending batch to orderer with IP = {}".format(ip))
            
            uniq_data_tuple = (int(batch["level_number"]), int(batch["cluster_id"]), int(batch["batch_id"]))

            if uniq_data_tuple not in unique_votes:
                unique_votes[uniq_data_tuple] = True
            
            if batch in receiver_q:
                receiver_q.remove(batch)
            
            receiver_q.append(batch)
    
    during_timeout_q.clear()

def flushDiffQ():
    """
    Forwards the batches from this queue to PEER ORDERERS and adds it to its own rec_q.
    Batches enter this queue from the output of the difference between receiver_q and the intersection batch
    """
    global unique_votes

    batchids_diff = getOnlyBatchIDs(diff_batch_q)

    orderer_ip_list = getOrdererIPs()
    
    for batch in diff_batch_q:
        for ip in orderer_ip_list:
            res = requests.post("http://" + ip + ":" + str(orderer_port) + "/api/orderer/receiveBatchFromPeerOrderer", json=batch)

            if res.status_code != 200:
                logging.error("Error sending batch to orderer with IP = {}".format(ip))
            
            uniq_data_tuple = (int(batch["level_number"]), int(batch["cluster_id"]), int(batch["batch_id"]))

            if uniq_data_tuple not in unique_votes:
                unique_votes[uniq_data_tuple] = True
            
            if batch in receiver_q:
                receiver_q.remove(batch)
            
            receiver_q.append(batch)

    diff_batch_q.clear()

def emptyReceiverQ():
    """
    Empties the receiver_q
    """

    batchids_rec = getOnlyBatchIDs(receiver_q)

    receiver_q.clear()

def intersect():
    global diff_batch_q
    global number_of_orderers

    if len(batched_batchvotes) > 0:
        number_of_orderers = getNumberOfOrderers()

        quorum = (number_of_orderers // 2) + 1
        
        logging.debug("Starting intersection")

        id_batch_mapping = {}
        ans = set()
        
        # extracted_batched_batchvotes = list(list(tuple(int))) where int is the type of any of these values (level_number, cluster_id, batch_id)
        extracted_batched_batchvotes, id_batch_mapping = extractAllIDs(batched_batchvotes, id_batch_mapping)

        batch_ids_freq = {}

        i = 0
        count = 0

        while i < len(extracted_batched_batchvotes) and len(extracted_batched_batchvotes[i]) == 0:
            i += 1
        
        if i < len(extracted_batched_batchvotes):
            for j in range(len(extracted_batched_batchvotes[i])):
                if extracted_batched_batchvotes[i][j] in batch_ids_freq:
                    batch_ids_freq[extracted_batched_batchvotes[i][j]] += 1
                else:
                    batch_ids_freq[extracted_batched_batchvotes[i][j]] = 1

            while i < len(extracted_batched_batchvotes):
                if len(extracted_batched_batchvotes[i]) == 0:
                    print("skipped batch i={} because it was empty".format(i))

                else:
                    for j in range(len(extracted_batched_batchvotes[i])):
                        if extracted_batched_batchvotes[i][j] in batch_ids_freq:
                            batch_ids_freq[extracted_batched_batchvotes[i][j]] += 1
                        else:
                            batch_ids_freq[extracted_batched_batchvotes[i][j]] = 1
                    
                    count += 1
                
                i += 1
        
        for key in batch_ids_freq:
            if batch_ids_freq[key] >= quorum:
                ans.add(key)
        
        if count >= quorum:
            transformed_rev_q = set(transformRecQ(receiver_q))
            
            diff_batch = transformed_rev_q.difference(ans)
            diff_batch_q = buildBatchFromMapping(list(diff_batch), id_batch_mapping)

            result = buildBatchFromMapping(list(ans), id_batch_mapping)
            result = sorted(result, key=lambda x: (x["level_number"], x["cluster_id"], x["batch_id"]))

            batch_ids = getOnlyBatchIDs(result)
            logging.debug("----------------------------------------------------------------")
            logging.debug("Intersection batch {}".format(batch_ids))
            logging.debug("----------------------------------------------------------------")

            id_batch_mapping.clear()

            return result
        
        else:
            transformed_rev_q = set(transformRecQ(receiver_q))
            
            diff_batch = transformed_rev_q.difference(ans)
            diff_batch_q = buildBatchFromMapping(list(diff_batch), id_batch_mapping)

            return list()
    
    else:
        return list()

def intersect_and_chooseRandOrd():
    intersection_batch = intersect()

    if len(intersection_batch) == 0:
        lb_ip_list = getLBIPs()

        for ip in lb_ip_list:
            res = requests.get("http://" + ip + ":" + str(lb_port) + "/api/lb/receiveAck")

            if res.status_code != 200:
                logging.error("Error sending ACK to LB with IP = {}".format(ip))

    # Find which random orderer will broadcast
    rand_ord_num = 0

    for vote in intersection_batch:
        rand_ord_num += (vote["batch_id"])
    
    number_of_orderers = getNumberOfOrderers()
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
                logging.error("Error broadcasting to bc{}".format(getBCNumber(ip)))
        
        logging.debug("Broadcast finished to lower level")

        lb_ip_list = getLBIPs()

        for ip in lb_ip_list:
            res = requests.get("http://" + ip + ":" + str(lb_port) + "/api/lb/receiveAck")

            if res.status_code != 200:
                logging.error("Error sending ACK to LB with IP = {}".format(ip))
    
    return

def send_batch_votes():
    global batched_batchvotes
    global number_of_orderers
    global PUT_IN_TIMEOUT_Q

    batchids_rec = getOnlyBatchIDs(receiver_q)
    batchids_timeout = getOnlyBatchIDs(during_timeout_q)
    batchids_diff = getOnlyBatchIDs(diff_batch_q)
    
    logging.debug("----------------------------------------------------------------")
    logging.debug("send_batch_votes Receiver_Q {}".format(batchids_rec))
    logging.debug("----------------------------------------------------------------")
    logging.debug("send_batch_votes Timeout_Q {}".format(batchids_timeout))
    logging.debug("----------------------------------------------------------------")
    logging.debug("send_batch_votes Diff_Q {}".format(batchids_diff))
    logging.debug("----------------------------------------------------------------")

    number_of_orderers = getNumberOfOrderers()
    batched_batchvotes.append(receiver_q)
    logging.debug("send_batch_votes len(batched_batchvotes) = {}".format(len(batched_batchvotes)))

    orderer_ip_list = getOrdererIPs()
    # logging.debug("Starting broadcast to peer orderers with the receiver_q")

    for ip in orderer_ip_list:
        data = {
            "batch_data": receiver_q
        }
        
        batchids_sent = getOnlyBatchIDs(data["batch_data"])

        logging.debug("----------------------------------------------------------------")
        logging.debug("send_batch_votes Data sent {} to orderer{}".format(batchids_sent, getOrdererNumber(ip)))
        logging.debug("----------------------------------------------------------------")
        
        res = requests.post("http://" + ip + ":" + str(orderer_port) + "/api/orderer/receiveBatchesFromPeerOrderer", json=data)

        if res.status_code != 200:
            logging.error("Failed to send receiver_q to peer orderer with IP = {}".format(ip))
    
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

        intersect_and_chooseRandOrd()
        
        batched_batchvotes.clear()

        PUT_IN_TIMEOUT_Q = False

        emptyReceiverQ()
        timeout_q_thread = threading.Thread(target=flushTimeoutQ)
        timeout_q_thread.start()
        diff_q_thread = threading.Thread(target=flushDiffQ)
        diff_q_thread.start()

def getOrdererNumber(ip):
    return int(ip.split(".")[-1]) - 1

def getBCNumber(ip):
    return int(ip.split(".")[-1]) - getNumberOfBC() - 1

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
            "batch_id": unique_int,
            "cluster_id": cluster_id_int,
            "level_number": level_number_int,
            ...
        }
    """

    global unique_votes
    
    if PUT_IN_TIMEOUT_Q:
        params = request.get_json()

        during_timeout_q.append(params)
    
    else:
        params = request.get_json()

        uniq_data_tuple = (int(params["level_number"]), int(params["cluster_id"]), int(params["batch_id"]))

        if uniq_data_tuple not in unique_votes:
            logging.debug("----------------------------------------------------------------")
            logging.debug("batchid = {} from bc{}".format(params["batch_id"], getBCNumber(request.remote_addr)))
            logging.debug("----------------------------------------------------------------")

            receiver_q.append(params)
            unique_votes[uniq_data_tuple] = True

            orderer_ip_list = getOrdererIPs()

            for ip in orderer_ip_list:
                res = requests.post("http://" + ip + ":80" + "/api/orderer/receiveBatchFromPeerOrderer", json=params)

                if res.status_code != 200:
                    logging.error("could not forward to peer orderer{}".format(getOrdererNumber(ip)))
                    return make_response("could not forward to peer orderer{}".format(getOrdererNumber(ip)), 400)

            return make_response("Added to orderer receiver_q", 200)
    
        logging.debug("----------------------------------------------------------------")
        logging.debug("Duplicate batch received from bc{}".format(getBCNumber(request.remote_addr)))
        logging.debug("----------------------------------------------------------------")
        
        return make_response("Duplicate batch received", 200)
    
    return make_response("Added to during_timeout_q", 200)

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
            "batch_id": unique_int,
            "cluster_id": cluster_id_int,
            "level_number": level_number_int,
            ...
        }
    """
    
    global unique_votes

    params = request.get_json()
    # logging.debug("Received vote data from peer orderer {}".format(params))
    # print("batchid = {} from IP = {}".format(params["batch_id"], request.remote_addr))

    uniq_data_tuple = (int(params["level_number"]), int(params["cluster_id"]), int(params["batch_id"]))

    # Detect duplicate votes
    if uniq_data_tuple not in unique_votes:
        logging.debug("----------------------------------------------------------------")
        logging.debug("batchid = {} from orderer{}".format(params["batch_id"], getOrdererNumber(request.remote_addr)))
        logging.debug("----------------------------------------------------------------")
        
        receiver_q.append(params)
        unique_votes[uniq_data_tuple] = True

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
    global number_of_orderers
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

        intersect_and_chooseRandOrd()
        
        batched_batchvotes.clear()

        PUT_IN_TIMEOUT_Q = False

        emptyReceiverQ()
        timeout_q_thread = threading.Thread(target=flushTimeoutQ)
        timeout_q_thread.start()
        diff_q_thread = threading.Thread(target=flushDiffQ)
        diff_q_thread.start()
    
    else:
        logging.debug("----------------------------------------------------------------")
        logging.debug("else part for the len(batched_batchvotes) == number_of_orderers")
        logging.debug("----------------------------------------------------------------")
    
    return make_response("Done calculating intersection batch", 200)

# ---------------------------------------- MAIN ----------------------------------------

def main():
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    return orderer

if __name__ == '__main__':
    main()

application = main()
