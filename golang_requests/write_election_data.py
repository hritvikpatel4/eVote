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

with open("election_data.txt", "w") as fileptr:
    for i in range(len(final_election_data_list) - 1):
        fileptr.write("{}::{}\n".format(final_election_data_list[i][0], final_election_data_list[i][2]))
    
    fileptr.write("{}::{}".format(final_election_data_list[-1][0], final_election_data_list[-1][2]))
    
    fileptr.flush()

print("Done!")
