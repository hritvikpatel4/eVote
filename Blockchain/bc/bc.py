# ---------------------------------------- IMPORT HERE ----------------------------------------

from flask import Flask, jsonify, make_response, request
import docker, hashlib, logging, os, random, re, requests, subprocess

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode()

LBC = Flask(__name__)
host = "0.0.0.0"
port = os.environ["CUSTOM_PORT"]
orderer_port = 80
LBC_LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
LEVEL_NUMBER = os.environ["CURRENT_LEVEL"] # This indicates the level of the cluster in the hierarchy

logging.basicConfig(filename=LBC_LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

def getOrdererIPs():
    """
    return -> list of ip addr
    """

    client = docker.from_env()
    container_list = client.containers.list()

    ip_list = []
    
    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            ip_list.append(out.output.decode().split("\n")[0])
    
    client.close()
    
    return ip_list

def generateHash(vote_list):
    # vote_list -> list generated from last line in the csv file
    # ["1", "narendra_modi", prevHash_SHA]
    
    s = ":::".join(vote_list)
    hashed_s = hashlib.sha256(s.encode()).hexdigest()

    return hashed_s

def writeToBlockchain(vote_id, candidate_id):
    f = open("lbc.csv", "a")

    # last_line 
    last_line = subprocess.run(["tail", "-1", "lbc.csv"], shell=False, capture_output=True).stdout.decode()
    # logging.debug("Last line: {}".format(last_line))
    vote_list = last_line.split(",")
    prev_hash = generateHash(vote_list)
    new_block = "{},{},{}\n".format(vote_id, candidate_id, prev_hash)
    # logging.debug("new block to write to csv: {}".format(new_block))
    f.write(new_block)
    f.close()
    os.sync()

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@LBC.route("/api/bc/receiveVoteFromLowLevel", methods=["POST"])
# Receive vote from lower level in the hierarchy and passes to orderer
def receiveVoteFromLowLevel():
    """
        input -> params which is received from lower level in the hierarchy
        return -> 200, 400
        
        params = {
            string: int
            
            "candidate_id_1": num_votes,
            "candidate_id_2": num_votes,
            "candidate_id_3": num_votes,
            ...
        }
    """

    params = request.get_json()
    
    logging.debug("Data {} received from lower level with IP = {}".format(params, request.remote_addr))

    # select a random orderer from the orderer_ip_list to forward the votedata received from lower level using params
    orderer_ip_list = getOrdererIPs()
    rand_ord_ip = random.choice(orderer_ip_list)

    res = requests.post("http://" + rand_ord_ip + ":" + str(orderer_port) + "/api/orderer/receiveFromBCNode", json=params)

    if res.status_code != 200:
        logging.error("Vote data forwarding to random orderer failed!")
        return make_response("vote error occurred", 400)
    
    else:
        logging.info("Vote data forwarded to random orderer with IP = {}".format(rand_ord_ip))
        return make_response("", 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    LBC.run(debug=True, port=port, host=host, use_reloader=False)
