# ---------------------------------------- IMPORT HERE ----------------------------------------

from custom_timer import RepeatedTimer
from flask import Flask, request, jsonify, make_response
import os, requests

# ---------------------------------------- CONFIGS ----------------------------------------

timerapp = Flask(__name__)
timer = None

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

def triggerBatching():
    timer.pause()
    
    res = requests.get("http://127.0.0.1" + ":80" + "/api/lb/triggerBatching")

    if res.status_code != 200:
        print("Error triggering batching API on the load_balancer")
    
    return

# ---------------------------------------- API ENDPOINTS ----------------------------------------

@timerapp.route("/resumeTimer", methods=["GET"])
# Resumes the timer
def resumeTimer():
    timer.start()

    return make_response("", 200)

# ---------------------------------------- MAIN ----------------------------------------

def main():
    print("timer started")
    timer = RepeatedTimer(int(os.environ["INTERVAL"]), triggerBatching)
    timer.start()

    return timerapp

if __name__ == '__main__':
    main()
