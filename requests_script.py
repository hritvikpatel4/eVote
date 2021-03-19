import requests, time
import random

for i in range(1, 21):
    x = random.randint(1, 5)
    
    data = {
        "level_number": 0,
        "cluster_id": 0,
        "batch_id": i,
        "c1": 0,
        "c2": 0,
        "c3": 0,
        "c4": 0,
        "c5": 0
    }

    data["c{}".format(str(x))] = 1

    # res = requests.post("http://146.148.43.144:80/castVote", json=data)
    res = requests.post("http://34.117.144.244:80/castVote", json=data)

    if res.status_code != 200:
        print("error sending request number {}".format(i))
    
    else:
        print("sent request number {}".format(i))

print("DONE!")
