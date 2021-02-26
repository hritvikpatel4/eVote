# ---------------------------------------- IMPORT HERE ----------------------------------------

from flask import Flask, jsonify, make_response, request
import csv, docker, hashlib, logging, os, random, re, requests, subprocess

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode()

BC = Flask(__name__)
host = "0.0.0.0"
port = os.environ["CUSTOM_PORT"]
orderer_port = 80
bc_port = 80
higher_level_port = 80
BC_LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
LEVEL_NUMBER = os.environ["CURRENT_LEVEL"] # This indicates the level of the cluster in the hierarchy
curr_tail_ptr = 1
prev_tail_ptr = 0
csv_header_fields = []
INIT_CSV_HEADER = False

# when sending to higher BC node, send values in the range [prev_tail_ptr + 1, curr_tail_ptr + 1)

logging.basicConfig(filename=BC_LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

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

def initCsvHeader(csv_header):
    global csv_header_fields
    
    csv_header_fields = list(csv_header.keys())
    csv_header_fields.append("prevHash")

    genesisBlock = {}

    for i in range(len(csv_header_fields)):
        genesisBlock[csv_header_fields[i]] = 0

    with open("bc.csv", "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_header_fields)
        writer.writeheader()
        writer.writerow(genesisBlock)

        csvfile.flush()

def generateHash(block):
    s = ":::".join(block)
    hashed_s = hashlib.sha256(s.encode()).hexdigest()

    return hashed_s

def writeToBlockchain(dataToWrite):
    global curr_tail_ptr

    with open("bc.csv", "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_header_fields)
        #do magic

        for block in dataToWrite:
            last_line = subprocess.run(["tail" "-1", "bc.csv"], shell=False, capture_output=True).stdout.decode()
            batch = last_line.split(",")
            prev_hash = generateHash(batch)

            new_block = block
            new_block["prevHash"] = prev_hash

            writer.writerow(new_block)

        csvfile.flush()
    
    ps = subprocess.Popen(('wc', 'bc.csv'), stdout=subprocess.PIPE)
    curr_tail_ptr = subprocess.check_output(('awk', 'END{print $1}'), stdin=ps.stdout).decode().strip("\n")
    ps.wait()

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@BC.route("/api/bc/receiveVoteFromLowLevel", methods=["POST"])
# Receive batch from lower level in the hierarchy and passes to orderer
def receiveVoteFromLowLevel():
    """
        input -> params which is received from lower level in the hierarchy
        return -> 200, 400
        
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
    
    # logging.debug("Data {} received from lower level with IP = {}".format(params, request.remote_addr))

    # select a random orderer from the orderer_ip_list to forward the votedata received from lower level using params
    orderer_ip_list = getOrdererIPs()
    rand_ord_ip = random.choice(orderer_ip_list)

    res = requests.post("http://" + rand_ord_ip + ":" + str(orderer_port) + "/api/orderer/receiveFromBCNode", json=params)

    if res.status_code != 200:
        logging.error("Vote data forwarding to random orderer failed!")
        return make_response("vote error occurred", 400)
    
    else:
        # logging.info("Vote data forwarded to random orderer with IP = {}".format(rand_ord_ip))
        return make_response("vote successfully forwarded to orderer", 200)

@BC.route("/api/bc/writeToBlockchain", methods=["POST"])
# Receive intersection batch from orderer and write to blockchain
def writeToBlockchain():
    params = request.get_json()["final_batch"]

    if len(params) == 0:
        return make_response("Empty batch received", 202)
    
    if not os.path.exists("bc.csv"):
        initCsvHeader(params[0])
    
    print("Got intersection batch from orderer {}".format(params))

    writeToBlockchain(params)

    return make_response("Successfully written to blockchain", 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    BC.run(debug=True, port=port, host=host, use_reloader=False)
