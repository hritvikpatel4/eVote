import requests, time

for i in range(1, 6):
    data = {
        "vote_id": i,
        "candidate_id": "narendra_modi"
    }
    requests.post("http://localhost:5000/castvote", json=data)
    time.sleep(1)

print("DONE!")