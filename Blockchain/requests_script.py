import requests, time

for i in range(1, 101):
    data = {
        "batch_id": i,
        "cluster_id": 0,
        "c1": 1,
        "c2": 0,
        "c3": 0,
        "c4": 0,
        "c5": 0
    }

    res = requests.post("http://146.148.43.144:80/castVote", json=data)

    if res.status_code != 200:
        print("error sending request number {}".format(i))
    
    else:
        print("sent request number {}".format(i))

print("DONE!")
