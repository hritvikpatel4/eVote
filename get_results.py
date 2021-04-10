import json, os, requests, subprocess

p1 = subprocess.Popen(("gcloud", "compute", "instances", "list", "--format=json"), stdout=subprocess.PIPE)
subprocess.check_output(("tee", "data.json"), stdin=p1.stdout)
p1.wait()

json_data = json.load(open("data.json", "r"))
ip_list = []

for i in range(len(json_data)):
    if "hbc" in json_data[i]["name"]:
        ip_list.append(json_data[i]["networkInterfaces"][0]["accessConfigs"][0]["natIP"])

result = []

for ip in ip_list:
    res = requests.get("http://" + ip + ":80" + "/getElectionResult")

    if res.status_code == 200:
            result.append(res.json())

temp_result = result[0]

for i in range(1, len(result)):
    for key in result[i].keys():
        temp_result[key] += result[i][key]

final_result = sorted(temp_result.items(), key=lambda item: -item[1])

print(final_result)

print("\n\tWinners:")

winners = []

if final_result[0][1] > final_result[1][1]:
    print("\t\t{} with a total of {} votes".format(final_result[0][0], final_result[0][1]))
    winners.append("{} with a total of {} votes".format(final_result[0][0], final_result[0][1]))

else:
    print("\t\t{} with a total of {} votes".format(final_result[0][0], final_result[0][1]))
    winners.append("{} with a total of {} votes".format(final_result[0][0], final_result[0][1]))
    try:
        i = 1
        while final_result[0][1] == final_result[i][1]:
            print("\t\t{} with a total of {} votes".format(final_result[i][0], final_result[i][1]))
            winners.append("{} with a total of {} votes".format(final_result[i][0], final_result[i][1]))
            i += 1
    
    except IndexError:
        pass

print()
os.remove("data.json")

final_result_list = []

for data in final_result:
    temp = list(data)

    final_result_list.append(temp)

json_result = {}
json_result["final_result"] = final_result_list
json_result["winners"] = winners

print(json.dumps(json_result, indent=2))
