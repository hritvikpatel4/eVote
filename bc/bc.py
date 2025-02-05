# ---------------------------------------- IMPORT HERE ----------------------------------------

from flask import Flask, jsonify, make_response, request
from google.cloud import storage
from google.cloud.storage.blob import Blob
from google.oauth2 import service_account
from cryptography.fernet import Fernet
import copy, csv, docker, hashlib, logging, os, random, re, requests, subprocess, threading

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode().strip("\n")

bc_number = int(node_name[len("bc"):])

bc = Flask(__name__)
host = "0.0.0.0"
orderer_port = 80
bc_port = 80
BC_LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
CURRENT_LEVEL = os.environ["CURRENT_LEVEL"] # This indicates the level of the cluster in the hierarchy
CLUSTER_ID = os.environ["CLUSTER_ID"]
HIGHEST_LEVEL = os.environ["HIGHEST_LEVEL"]
HIGHER_LEVEL_IP = os.environ["HIGHER_LEVEL_IP"] if CURRENT_LEVEL < HIGHEST_LEVEL else ""
csv_header_fields = []
INIT_CSV_HEADER = False
key_filename = "{}_{}".format("bc", bc_number)
dest_bc_csv_filename = "{}_{}.csv".format(CURRENT_LEVEL, CLUSTER_ID)
gcs_cred = service_account.Credentials.from_service_account_file("./capstone-304713.json")
storage_client = storage.Client(credentials = gcs_cred)
gcs_bucket = storage_client.bucket("evote-cdn")

logging.basicConfig(filename=BC_LOG_FILE, filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

def initFernet():
    encryption_key = Fernet.generate_key()
    
    with open(key_filename, "wb") as fileptr:
        fileptr.write(encryption_key)

        fileptr.flush()

    return

def loadFernet():
    return open(key_filename, "rb").read()

def getDBIPs():
    """
    return -> list of ip addr
    """

    client = docker.from_env()
    container_list = client.containers.list()

    ip_list = []
    
    for container in container_list:
        if re.search("^db[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            ip_list.append(out.output.decode().split("\n")[0])
    
    client.close()
    
    return ip_list

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

def getNumberOfBC():
    counter = 0
    client = docker.from_env()
    container_list = client.containers.list()

    for container in container_list:
        if re.search("^bc[1-9][0-9]*", container.name):
            counter += 1
    
    client.close()
    return counter

def initCsvHeader(csv_header):
    global csv_header_fields
    
    csv_header_fields = list(csv_header.keys())
    csv_header_fields.append("prevHash")

    genesisBlock = {}

    for i in range(len(csv_header_fields)):
        genesisBlock[csv_header_fields[i]] = 0

    with open("bc.csv", "ab") as csvfile:
        fernet_key = Fernet(loadFernet())

        csvfile.write(fernet_key.encrypt((",".join(csv_header_fields)).encode()) + b"\n")
        
        raw_s = ""

        for i in csv_header_fields:
            raw_s += (str(genesisBlock[i]) + ",")
        
        raw_s = raw_s[:-1]

        csvfile.write(fernet_key.encrypt(raw_s.encode()) + b"\n")

        csvfile.flush()

def generateHash(block):
    s = ":::".join(block)
    hashed_s = hashlib.sha256(s.encode()).hexdigest()

    return hashed_s

def writeToCSV(dataToWrite):
    with open("bc.csv", "ab") as csvfile:
        fernet_key = Fernet(loadFernet())
        
        for i in range(len(dataToWrite)):
            last_line = subprocess.run(["tail", "-1", "bc.csv"], shell=False, capture_output=True).stdout
            prev_batch = ((fernet_key.decrypt(last_line)).decode()).strip("\n")
            prev_hash = generateHash(prev_batch)
            
            dataToWrite[i]["prevHash"] = prev_hash
            
            raw_s = ""

            for header in csv_header_fields:
                raw_s += (str(dataToWrite[i][header]) + ",")
            
            raw_s = raw_s[:-1]

            csvfile.write(fernet_key.encrypt(raw_s.encode()) + b"\n")

            csvfile.flush()
        
        csvfile.flush()

    return

# batch -> list of dict
def passToHigherLevel(batch):
    rand_bc_num = 0
    
    for i in range(len(batch)):
        rand_bc_num += batch[i]["batch_id"]
    
    rand_bc_num = (rand_bc_num % getNumberOfBC()) + 1
    
    if rand_bc_num == int(bc_number) and (CURRENT_LEVEL < HIGHEST_LEVEL):
        ans = batch[0]

        for i in range(1, len(batch)):
            for key in batch[i].keys():
                if key not in ["batch_id", "cluster_id", "level_number"]:
                    ans[key] += batch[i][key]
        
        count = 0

        for key in ans.keys():
            if key not in ["batch_id", "cluster_id", "level_number"]:
                count += ans[key]

        ans["level_number"] = int(CURRENT_LEVEL)
        ans["cluster_id"] = int(CLUSTER_ID)
        db_ip = getDBIPs()[0]
        batch_id_res = requests.get("http://" + db_ip + ":80" + "/api/db/generateBatchID")
        batch_id = batch_id_res.json()["batchid"]
        ans["batch_id"] = int(batch_id)

        res = requests.post(HIGHER_LEVEL_IP + "/castVote", json=ans)

        if res.status_code != 200:
            logging.error("Passing to higher level FAILED!")
    
    return

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@bc.route("/api/bc/receiveVoteFromLowLevel", methods=["POST"])
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
            "batch_id": unique_int,
            "cluster_id": cluster_id_int,
            "level_number": level_number_int,
            ...
        }
    """
    params = request.get_json()
    
    # logging.debug("Data {} received from lower level with IP = {}".format(params, request.remote_addr))

    # select a random orderer from the orderer_ip_list to forward the votedata received from lower level using params
    rand_ord_ip = random.choice(orderer_ip_list)

    res = requests.post("http://" + rand_ord_ip + ":" + str(orderer_port) + "/api/orderer/receiveFromBCNode", json=params)

    if res.status_code != 200:
        logging.error("Vote data forwarding to random orderer failed!")
        return make_response("vote error occurred", 400)
    
    else:
        # logging.info("Vote data forwarded to random orderer with IP = {}".format(rand_ord_ip))
        return make_response("vote successfully forwarded to orderer", 200)

@bc.route("/api/bc/writeToBlockchain", methods=["POST"])
# Receive intersection batch from orderer and write to blockchain
def writeToBlockchain():
    params = request.get_json()["final_batch"]

    if len(params) == 0:
        return make_response("Empty batch received", 200)
    
    if not os.path.exists("bc.csv"):
        initCsvHeader(params[0])
    
    batchids = []

    for i in params:
        batchids.append(i["batch_id"])

    writeToCSV(copy.deepcopy(params))
    
    passToHigherLevel(copy.deepcopy(params))

    return make_response("Successfully written to blockchain", 200)

@bc.route("/api/bc/calculateElectionResult", methods=["GET"])
# Sends the tallied election result from this cluster to the load_balancer
def calculateElectionResult():
    if isinstance(gcs_bucket.get_blob("input/" + dest_bc_csv_filename), Blob):
        return make_response("File already uploaded", 300)
    
    else:
        with open("bc.csv", "rb") as fileptr:
            fernet_key = Fernet(loadFernet())
            
            with open("{}_bc.csv".format("decrypted"), "w") as temp_ptr:
                while True:
                    data = fileptr.readline()

                    if not data:
                        break #EOF

                    decrypted_data = fernet_key.decrypt(data).decode().strip("\n")
                    temp_ptr.write(decrypted_data + "\n")

                    temp_ptr.flush()
        
        file_blob = gcs_bucket.blob("input/" + dest_bc_csv_filename)
        file_blob.upload_from_filename("decrypted_bc.csv")

        os.remove("decrypted_bc.csv")

    return make_response("Uploaded csv", 202)

# ---------------------------------------- MAIN ----------------------------------------

orderer_ip_list = getOrdererIPs()

def main():
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))
    
    initFernet()

    return bc

if __name__ == '__main__':
    main()

application = main()
