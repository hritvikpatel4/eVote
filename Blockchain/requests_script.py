import requests, time

for i in range(1, 6):
    data = {
        "vote_id": i,
        "candidate_id": i+10
    }
    requests.post("http://35.238.254.36:80/castvote", json=data)
    time.sleep(1)

print("DONE!")