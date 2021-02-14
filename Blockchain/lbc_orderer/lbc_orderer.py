# ---------------------------------------- IMPORT HERE ----------------------------------------

from flask import Flask, jsonify, make_response, request
from queue import Queue
import docker, json, logging, os, re, requests, subprocess, threading, time

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode()

current_orderer_name = node_name

orderer = Flask(__name__)
host = "0.0.0.0"
port = os.environ["CUSTOM_PORT"]

ORDERER_LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)

logging.basicConfig(filename=ORDERER_LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

receiver_q = Queue(maxsize=0)   # This Q contains votes from LBC to orderer
batchvotes = []                 # This is a structure which stores the vote data. IT'S A LIST(LIST(DICT)) eventually
orderer_sets_received = 0       # This is a counter to check whether we have received all the batches from other orderers on the network
number_of_orderers = 3          # total number of orderers in each hierarchy
orderer_number = 0              # the current orderer number which is running
unique_votes = {}               # This is a structure which is used for detecting duplicate votes

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

'''
When timer hits 5 minutes, everything is transferred from rec_q to validvotes_q.
Orderer nodes broadcast their validvotes_q's to each other. The intersection is calculated,
and broadcast to all the LBC nodes. The LBC nodes add these votes to their blockchains.
In each orderer, all votes that are not part of the intersection are pushed back into their
respective rec_q's, following which the validvotes_q's are emptied.

- AS, HP convinced by some explanation given by AP
'''

# Convert any queue.Queue to a list
def convertQueueToList(receiver_q):
    temp = []
    
    while not receiver_q.empty():
        temp.append(receiver_q.get())
    
    return temp

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

# Send the receiver_q as a list to all peer orderers
def send_batch_votes():
    # convert the internal receiver_queue to a list
    batch_votedata = convertQueueToList(receiver_q)

    logging.debug("batch_votedata: {}".format(batch_votedata))
    
    # add the batched votedata to the batchvotes list
    global batchvotes
    batchvotes.append(batch_votedata)

    logging.debug("batchvotes: {}".format(batchvotes))
    
    data = {
        "get_batch": batch_votedata
    }

    client = docker.from_env()
    container_list = client.containers.list()

    # ip_list contains ip addresses of peer orderers (all orderers but itself)
    ip_list = []

    logging.debug("Sending batch votedata to all the peer orderers")
    
    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name) and container.name != current_orderer_name:
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            ip_list.append(out.output.decode().split("\n")[0])
    
    # broadcast the current vote batch to all peer orderers (all orderers but itself)
    for ip in ip_list:
        requests.post("http://" + ip + ":80" + "/api/orderer/receivebatch", json=data)
    
    logging.debug("Sent batch votedata to all the peer orderers")

# Intersect the batched votes
def union_votes():
    global batchvotes
    
    if len(batchvotes) > 0:
        # use the set intersection operation
        # init ans to the first entry in batchvotes
        transformed_batchvotes = transformBatch(batchvotes)
        logging.debug("batchvotes: {}".format(batchvotes))
        logging.debug("transformed_batchvotes: {}".format(transformed_batchvotes))
        ans = set(transformed_batchvotes[0])
        logging.debug("ans: {}".format(ans))
        
        for batch in transformed_batchvotes:
            logging.debug("Current batch: {}".format(batch))
            ans = ans.union(set(batch))
        
        logging.debug("ans: {}".format(ans))
        ans = deTransformBatch(list(ans))
        logging.debug("ans 'detransformed': {}".format(ans))
        
        # convert set to list and sort it based on vote_id
        # ans = list(ans).sort(key=lambda x: x["vote_id"])
        ans = sorted(ans, key=lambda x: x["vote_id"])
        logging.debug("ans 'sorted': {}".format(ans))
        
        logging.debug("Intersecion batch {}".format(ans))
        
        return ans

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@orderer.route("/api/orderer/receivelbc", methods=["POST"])
# Receive vote from LBC node and broadcast to peer orderers
def receiveVoteFromLBC():
    """
        params = {
            "vote_id": int,
            "candidate_id": str
        }
    """
    params = request.get_json()
    logging.info("Params {} received from LBC with IP {}".format(params, request.remote_addr))

    # add the vote into the queue
    receiver_q.put(params)

    client = docker.from_env()
    container_list = client.containers.list()

    # ip_list contains ip addresses of all orderers
    ip_list = []
    
    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name) and container.name != current_orderer_name:
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            ip_list.append(out.output.decode().split("\n")[0])
    
    logging.debug("Now broadcasting to peer orderers")

    # broadcast vote to all peer orderers by calling their receiveVoteFromOrderer APIs
    for ip in ip_list:
        requests.post("http://" + ip + ":80" + "/api/orderer/receiveorderer", json=params)
    
    logging.debug("Broadcast Finished")

    return make_response("Added to orderer receive queue", 200)

@orderer.route("/api/orderer/receiveorderer", methods=["POST"])
# Receives vote from peer orderers.
# The vote comes from a peer orderer that itself received from a LBC node
def receiveVoteFromOrderer():
    """
        params = {
            "vote_id": int,
            "candidate_id": str
        }
    """
    params = request.get_json()
    logging.debug("Received vote data from peer orderer")

    # Detect duplicate votes
    if params["vote_id"] not in unique_votes:
        receiver_q.put(params)
        unique_votes[params["vote_id"]] = True

        return make_response("Added vote into receiver_q", 200)

    return make_response("Duplicate vote received", 400)

@orderer.route("/api/orderer/startbatching", methods=["GET"])
# Receives the decision to start batching
def startBatching():
    # execute the batching of votes
    logging.info("Running send_batch_votes()")
    send_batch_votes()

    return make_response("", 200)

@orderer.route("/api/orderer/receivebatch", methods=["POST"])
# Receives all vote sets from peer orderers. Finds the intersection [on every 2 minute interval]
# and choses a random orderer to broadcast the chosen set to all LBC nodes
def receiveBatchVotesFromOrderers():
    global orderer_sets_received
    global batchvotes

    orderer_sets_received += 1
    params = request.get_json()

    logging.debug("Batch vote data received from IP {}".format(request.remote_addr))
    
    batch_data = params["get_batch"]
    batchvotes.append(batch_data)

    client = docker.from_env()
    container_list = client.containers.list()

    counter = 0

    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name):
            counter += 1

    # update the count of orderers
    number_of_orderers = counter
    client.close()
    
    # once all vote batches from all peer orderers except itself have been received, find intersection & broadcast to all LBC nodes
    if orderer_sets_received == number_of_orderers - 1:
        intersection_batch = union_votes()

        logging.info("Checking which orderer will broadcast the final batch")

        # the following number is used to generate the orderer node which broadcasts in the end
        rand_ord = 0

        for vote in intersection_batch:
            rand_ord += (vote["vote_id"] + vote["candidate_id"])
        
        rand_ord = (rand_ord % number_of_orderers) + 1

        logging.debug("Random orderer{} will broadcast".format(rand_ord))

        # if the current orderer is the chosen one, then execute the following logic
        if rand_ord == int(orderer_number):
            data = {
                "final_batch": intersection_batch
            }

            client = docker.from_env()
            container_list = client.containers.list()

            logging.debug("I will be broadcasting the final batch. My name is orderer{}".format(rand_ord))

            # ip_list contains ip addresses of all the LBC nodes
            ip_list = []
            
            for container in container_list:
                if re.search("^lbc[1-9][0-9]*", container.name):
                    out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
                    ip_list.append(out.output.decode().split("\n")[0])

            # broadcast to all the LBC
            for ip in ip_list:
                requests.post("http://" + ip + ":80" + "/api/lbc/recordvotes", json=data)

            logging.info("Broadcasting final batch to LBC DONE")

            # Send ack back to load balancer that intersection is done
            container_list = client.containers.list()
            ip_list = []
            
            for container in container_list:
                if re.search("^load_balancer[1-9][0-9]*", container.name):
                    out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
                    ip_list.append(out.output.decode().split("\n")[0])

            for ip in ip_list:
                requests.get("http://" + ip + ":8080" + "/api/lb/receiveack")
            
            client.close()

        # re-initialize global variables
        orderer_sets_received = 0
        batchvotes = []
    
    return make_response("", 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
    orderer_name = process_output.stdout.decode()
    orderer_number = orderer_name[len("orderer"):]
    
    # logging.info("Timer started!")
    # init_timer()

    orderer.run(debug=True, port=port, host=host, use_reloader=False)
