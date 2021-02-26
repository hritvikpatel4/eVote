import requests, time

for i in range(1, 11):
    data = {
        "batch_id": i,
        "1": 1,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0
    }
    requests.post("http://146.148.43.144:80/castVote", json=data)
    print("sent request number {}".format(i))

print("DONE!")