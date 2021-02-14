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
LBC_LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)

logging.basicConfig(filename=LBC_LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

def generateHash(vote_list):
    # vote_list -> list generated from last line in the csv file
    # ["1", "narendra_modi", prevHash_SHA]
    
    s = ":::".join(vote_list)
    hashed_s = hashlib.sha256(s.encode()).hexdigest()

    return hashed_s

def writeToBlockchain(vote_id, candidate_id):
    f = open("lbc.csv", "ab")

    # last_line 
    last_line = subprocess.run(["tail", "-1", "lbc.csv"], shell=False, capture_output=True).stdout.decode()
    logging.debug("Last line: ", last_line)
    vote_list = last_line.split(",")
    prev_hash = generateHash(vote_list)
    new_block = "{},{},{}\n".format(vote_id, candidate_id, prev_hash)
    logging.debug("new block to write to csv: ", new_block)
    f.write(new_block)
    f.close()
    os.sync()

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@LBC.route("/api/lbc/receivevote", methods=["POST"])
# Receive vote from web server and passes to orderer
def receiveVoteFromWebServer():
    """
        params = {
            "vote_id": int,
            "candidate_id": int
        }
    """

    params = request.get_json()
    
    logging.debug("Params {} received from webserver {}".format(params, request.remote_addr))

    vote_id = params["vote_id"] # unique number assigned to the vote by the DB
    candidate_id = params["candidate_id"] # unique number assigned to the candidate voted for by the DB

    client = docker.from_env()
    container_list = client.containers.list()

    ip_list = []
    
    for container in container_list:
        if re.search("^orderer[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            ip_list.append(out.output.decode().split("\n")[0])

    # select a random orderer from the ip_list to forward the votedata received from webserver using params
    rand_ord_ip = random.choice(ip_list)
    
    logging.debug("Random orderer with IP {} selected".format(rand_ord_ip))

    requests.post("http://" + rand_ord_ip + ":80" + "/api/orderer/receivelbc", json=params)

    logging.info("Vote data forwarded to random orderer")
    client.close()

    return make_response("", 200)

@LBC.route("/api/lbc/recordvotes", methods=["POST"])
# Stores batch of votes from orderer in its local blockchain
def recordVotesFromOrderer():
    params = request.get_json()
    
    logging.debug("Params {} received from peer orderer {}".format(params, request.remote_addr))
    
    logging.info("Writing batch vote data to csv file")
    
    batch_vote = params["final_batch"]

    for vote in batch_vote:
        vote_id = vote["vote_id"]
        candidate_id = vote["candidate_id"]

        writeToBlockchain(vote_id, candidate_id)
    
    logging.info("Finished Writing vote data to csv file")

    return make_response("", 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    LBC.run(debug=True, port=port, host=host, use_reloader=False)
