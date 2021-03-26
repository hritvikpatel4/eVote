# ---------------------------------------- IMPORT HERE ----------------------------------------

from custom_timer import RepeatedTimer
from flask import Flask, request, jsonify, make_response
import os, requests

# ---------------------------------------- CONFIGS ----------------------------------------

timerapp = Flask(__name__)

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

def triggerBatching():
    countdowntimer.pause()
    
    res = requests.get("http://0.0.0.0:80" + "/api/lb/triggerBatching")

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
