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

print(ip_list)

for ip in ip_list:
    res = requests.get("http://" + ip + ":80" + "/getElectionResult")

    print(res.json())
