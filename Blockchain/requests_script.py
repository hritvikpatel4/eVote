import requests, time

for i in range(1, 21):
    data = {
        "vote_id": i,
        "candidate_id": 20
    }
    requests.post("http://146.148.43.144:80/castvote", json=data)

print("DONE!")