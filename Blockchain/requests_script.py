import requests, time

for i in range(61, 71):
    data = {
        "batch_id": i,
        "c1": 1,
        "c2": 0,
        "c3": 0,
        "c4": 0,
        "c5": 0
    }

    requests.post("http://146.148.43.144:80/castVote", json=data)
    
    print("sent request number {}".format(i))

print("DONE!")