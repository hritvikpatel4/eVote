# ---------------------------------------- IMPORT HERE ----------------------------------------

from datetime import datetime, timedelta
from flask import Flask, jsonify, request
import docker, os, random, re, requests, threading

# ---------------------------------------- CONFIGS ----------------------------------------

process_output = subprocess.run(["hostname"], shell=False, capture_output=True)
node_name = process_output.stdout.decode().split("\n")[0]
node_ip = subprocess.run(["awk", "END{print $1}", "/etc/hosts"], shell=False, capture_output=True).stdout.decode()

app = Flask(__name__)
host = "0.0.0.0"
port = os.environ["CUSTOM_PORT"]
portnum = 80 # fixed port no. on which all lbc and orderer containers run their Flask servers
LOG_FILE = "/usr/src/app/logs/{}.log".format(node_name)
next_timeout = None

logging.basicConfig(filename=LOG_FILE, encoding='utf-8', filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

# Timer function
def timerfunc():
    global next_timeout

    while True:
        while datetime.now() != next_timeout:
            pass
        
        next_timeout = datetime.now() + timedelta(minutes=2)

        logging.debug("Timeout! Updating the number of orderers and executing batching of votes")

        # client = docker.from_env()
        # container_list = client.containers.list()

        # counter = 0
        
        # for container in container_list:
        #     if re.search("^orderer[1-9][0-9]*", container.name):
        #         counter += 1
        
        # # update the count of orderers
        # number_of_orderers = counter

# Init timer
def init_timer():
    global timer

    if not timer:
        timer = threading.Thread(target = timerfunc)
        timer.start()

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@app.route('/castvote', methods =['POST'])
def castVote():
    client = docker.from_env()
    clist = client.containers.list()

    ip_list = []

    for container in clist:
        if re.search("^lbc[1-9][0-9]*", container.name):
            out = container.exec_run("awk 'END{print $1}' /etc/hosts", stdout=True)
            ip_list.append(out.output.decode().split("\n")[0])

    if(len(ip_list) == 0):
        return jsonify({"status": "No LBC containers running"}, 400)

    rand_lbc_ip = random.choice(ip_list)
    print("ip list = ", ip_list)

    params = request.get_json()

    requests.post("http://" + rand_lbc_ip + ":" + str(portnum) + "/api/lbc/receivevote", json=params)
    print("rand lbc ip = ", rand_lbc_ip)
    print()

    return jsonify({}, 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    logging.info("{} has started. It's IP is {}".format(node_name, node_ip))

    next_timeout = datetime.now() + timedelta(minutes=2)
    init_timer()
    
    app.run(debug=True, host=host, port=port, use_reloader=False)
