# ---------------------------------------- IMPORT HERE ----------------------------------------

from custom_timer import RepeatedTimer
from flask import Flask, request, make_response
import docker, os, re, requests

# ---------------------------------------- CONFIGS ----------------------------------------

timerapp = Flask(__name__)

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

def getLBIPs():
    """
    returns list of ip addr
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

def triggerBatching():
    countdowntimer.pause()

    lb_ip = getLBIPs()[0]
    
    res = requests.get("http://" + lb_ip + ":80" + "/api/lb/triggerBatching")

    if res.status_code != 200:
        print("Error triggering batching API on the load_balancer")
    
    return

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@timerapp.route("/resumeTimer", methods=["GET"])
# Resumes the timer
def resumeTimer():
    countdowntimer.start()

    return make_response("", 200)

# ---------------------------------------- MAIN ----------------------------------------

countdowntimer = RepeatedTimer(int(os.environ["INTERVAL"]), triggerBatching)

def main():
    print("timer started")
    countdowntimer.start()

    timerapp.run(host="0.0.0.0", port=80, use_reloader=False, debug=False)
    # return timerapp

if __name__ == '__main__':
    main()
