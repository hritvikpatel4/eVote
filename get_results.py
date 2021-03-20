import json, requests, subprocess

p1 = subprocess.Popen(("gcloud", "compute", "instances", "list", "--format=json"), stdout=subprocess.PIPE)
subprocess.check_output(("tee", "data.json"), stdin=p1.stdout)
p1.wait()

json_data = json.load(open("data.json", "r"))
ip_list = []

for i in range(len(json_data)):
    if "hbc" in json_data[i]["name"]:
        print(json_data[i]["name"])
        print(json_data[i]["networkInterfaces"][0]["accessConfigs"][0]["natIP"])
        ip_list.append(json_data[i]["networkInterfaces"][0]["accessConfigs"][0]["natIP"])

result = []

for ip in ip_list:
    res = requests.get("http://" + ip + ":80" + "/getElectionResult")

    result.append(res.json())

temp_result = result[0]

for i in range(1, len(result)):
    for key in result[i].keys():
        temp_result[key] += result[i][key]

final_result = dict(sorted(temp_result.items(), key=lambda item: item[1]))

print(json.dumps(final_result, indent=4)
