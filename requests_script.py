import requests, time
import random

db_ip = "http://34.66.242.58:80"

election_data_fetch = {
    "operation": "SELECT",
    "columns": "*",
    "tablename": "votingperiod",
    "where": ["1=1"]
}

election_data = requests.post(db_ip + "/api/db/read", json=election_data_fetch)
election_data_string = election_data.text.replace(" ", "").replace("\n", "")
indices = [i for i, x in enumerate(election_data_string) if x == "]"]
indices.pop()
indices.insert(0, 0)
election_data_list = [election_data_string[indices[i]: indices[i + 1]] for i in range(len(indices) - 1)]
for i in range(len(election_data_list)):
    election_data_list[i] = election_data_list[i].replace("[", "").replace("]", "").strip(",")
final_election_data_list = []
for i in election_data_list:
    temp = i.split(",")
    for j in range(len(temp)):
        temp[j] = temp[j].replace('"', "")
    final_election_data_list.append(temp)

for i in range(1, 501):
    data = {
        "level_number": 0,
        "cluster_id": 0,
        "batch_id": i
    }

    for j in range(len(final_election_data_list)):
        temp = "{}::{}".format(final_election_data_list[j][0], final_election_data_list[j][2])
        
        data[temp] = 0

    x = random.randint(0, len(final_election_data_list) - 1)
    lucky_candidate = final_election_data_list[x][2]
    lucky_party = final_election_data_list[x][0]
    
    data["{}::{}".format(lucky_party, lucky_candidate)] = 1

    # res = requests.post("http://146.148.43.144:80/castVote", json=data)
    res = requests.post("http://34.117.144.244:80/castVote", json=data)

    if res.status_code != 200:
        print("error sending request number {}".format(i))
    
    else:
        print("sent request number {}".format(i))
        # print(data)

print("DONE!")
