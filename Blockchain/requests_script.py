import requests, time

for i in range(30, 36):
    data = {
        "vote_id": i,
        "candidate_id": 20
    }
    requests.post("http://35.238.254.36:80/castvote", json=data)
    time.sleep(1)

print("DONE!")