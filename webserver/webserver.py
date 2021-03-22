# ---------------------------------------- IMPORT HERE ----------------------------------------

from flask import render_template, Flask, json, jsonify, make_response, request, send_from_directory
from google.cloud import storage
from google.oauth2 import service_account
from werkzeug.utils import secure_filename
import datetime, os, random, requests, string, time

# ---------------------------------------- CONFIGS ----------------------------------------

webserver = Flask(__name__)
port = os.environ["CUSTOM_PORT"]
host = "0.0.0.0"
db_ip = os.environ["DB_IP"]
CLUSTER_ID = os.environ["CLUSTER_ID"]
CURRENT_LEVEL = os.environ["CURRENT_LEVEL"]
HIGHEST_LEVEL = os.environ["HIGHEST_LEVEL"]
VOTE_ENDPOINT = os.environ["VOTE_ENDPOINT"]
UPLOAD_FOLDER = "./upload"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
webserver.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
webserver.config['CUSTOM_STATIC_CDN'] = "/upload/"
gcs_cred = service_account.Credentials.from_service_account_file("./capstone-304713.json")
storage_client = storage.Client(credentials = gcs_cred)
gcs_bucket = storage_client.bucket("evote-cdn")

# ---------------------------------------- ADMIN SETTINGS ----------------------------------------

# Admin database
# Format
# key: "admin id"
# value: "admin masterpwd"
details = {
    "admin_1": "admin@12",
    "admin_2": "admin@123"
}

# ---------------------------------------- WEB SERVER ENDPOINTS ----------------------------------------

@webserver.route("/health")
# API to handle health requests from google
def health():
    return make_response("Alive and running!", 200)

@webserver.route("/upload/<path:filename>")
# API to handle requests for the static files for the voting page
def upload(filename):
    file_blob = gcs_bucket.get_blob(filename)
    return file_blob.generate_signed_url(version='v4', expiration=datetime.timedelta(hours=1))

@webserver.route("/", methods=["GET"])
# API to handle the requests for the index page
def requestIndexPage():
    return render_template("index.html")

@webserver.route("/api/login", methods=["POST"])
# API to handle voter login
def loginVoter(voter_id = None, voter_dob = None, voter_secretkey = None):
    # Get voter login details
    params = request.get_json()
    voter_id = params["voter_id"]
    voter_dob = params["voter_dob"]
    voter_secretkey = params["voter_secretkey"]

    # Check if entered details match the database entries
    data = {
        "operation": "SELECT",
        "columns": "*",
        "tablename": "voters",
        "where": ["voter_id='{}'".format(voter_id), "voter_secretkey='{}'".format(voter_secretkey), "voter_dob='{}'".format(voter_dob)]
    }
    
    code = requests.post(db_ip + "/api/db/read", json=data)

    if code.status_code != 400:
        return make_response("Auth successful", 200)
    
    # Auth error
    return make_response("Auth Failed", 400)

@webserver.route("/api/login/ui", methods=["GET"])
# API to send the voting page after voter successfully authenticates
def requestVoterUI(voter_id = None, voter_secretkey = None):
    # Get voter context
    args = request.args
    voter_id = args["id"]
    voter_secretkey = args["ctx"]

    # Check if the context is correct with the database
    data = {
        "operation": "SELECT",
        "columns": "*",
        "tablename": "voters",
        "where": ["voter_id='{}'".format(voter_id), "voter_secretkey='{}'".format(voter_secretkey)]
    }

    code = requests.post(db_ip + "/api/db/read", json=data)

    if code.status_code != 400:
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
        
        party_names = []
        party_images = []
        rep_names = []
        rep_images = []

        for i in len(final_election_data_list):
            party_names.append(final_election_data_list[i][0])
            party_images.append(final_election_data_list[i][1])
            rep_names.append(final_election_data_list[i][2])
            rep_images.append(final_election_data_list[i][3])

        # return render_template("voting.html", voter_id = voter_id, voter_secretkey = voter_secretkey, election_data = json.dumps(final_election_data_list), election_data_size = len(final_election_data_list))
        return render_template("voting.html", voter_id = voter_id, voter_secretkey = voter_secretkey, party_names = json.dumps(party_names), party_images = json.dumps(party_images), rep_names = json.dumps(rep_names), rep_images = json.dumps(rep_images), data_size = len(final_election_data_list))
    
    # Wrong context sent
    return make_response("Bad Request", 400)

@webserver.route("/api/submitvote", methods=["POST"])
# API to handle the vote submitted by voter
def submitVote(voter_id = None, voter_secretkey = None):
    # Get voter details and who he/she has voted for
    args = request.args
    voter_id = args["id"]
    voter_secretkey = args["ctx"]
    
    # party_name and representative_name can now be used for the blockchain
    voted_for = request.form.get("vote")
    party_name, representative_name = voted_for.split(":::")

    # Check if voter exists with given credentials
    data1 = {
        "operation": "SELECT",
        "columns": "*",
        "tablename": "voters",
        "where": ["voter_id='{}'".format(voter_id), "voter_secretkey='{}'".format(voter_secretkey)]
    }

    code1 = requests.post(db_ip + "/api/db/read", json=data1)

    # Voter exists! Now check if he has already casted a vote
    if code1.status_code != 400:
        data2 = {
            "operation": "SELECT",
            "columns": ["already_voted"],
            "tablename": "voters",
            "where": ["voter_id='{}'".format(voter_id), "voter_secretkey='{}'".format(voter_secretkey)]
        }

        code2 = requests.post(db_ip + "/api/db/read", json=data2).json()

        # Voter did not cast vote yet
        if code2[0][0] == 0:
            vote_data = {
                "level_number": int(CURRENT_LEVEL),
                "cluster_id": int(CLUSTER_ID)
            }

            batch_id_res = requests.get(db_ip + "/api/db/generateBatchID")
            batch_id = batch_id_res.json()["batchid"]
            vote_data["batch_id"] = int(batch_id)

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

            print(voted_for)
            print(final_election_data_list)

            for i in range(len(final_election_data_list)):
                temp = "{}::{}".format(final_election_data_list[i][0], final_election_data_list[i][2])
                
                vote_data[temp] = 0
            
            vote_data["{}::{}".format(party_name, representative_name)] = 1

            cast_vote_res = requests.post(VOTE_ENDPOINT + "/castVote", json=vote_data)

            if cast_vote_res.status_code != 200:
                return make_response("Error!", 400)

            data3 = {
                "operation": "UPDATE",
                "tablename": "voters",
                "column": "already_voted",
                "update_value": 1
            }

            code3 = requests.post(db_ip + "/api/db/modify", json=data3)

            if code3.status_code != 200:
                return make_response("Error!", 400)
        
        # Voter already casted vote
        else:
            return make_response("Error!", 400)
    
    # Voter does not exist
    else:
        return make_response("Error!", 400)
    
    # Everything worked perfectly, so return success!
    return make_response("Success!", 200)

@webserver.route("/register", methods=["GET"])
# API to handle the requests for the register page
def requestRegisterPage():
    return render_template("register.html")

@webserver.route("/api/register", methods=["POST"])
# API to handle voter registrations
def registerVoter(voter_id = None, voter_name = None, voter_dob = None, voter_secretkey = None):
    # Get register form data
    params = request.get_json()
    voter_id = params["voter_id"]
    voter_name = params["voter_name"]
    voter_dob = params["voter_dob"]

    # Check if voter already exists
    data = {
        "operation": "SELECT",
        "columns": "*",
        "tablename": "voters",
        "where": ["voter_id='{}'".format(voter_id)]
    }
    
    code = requests.post(db_ip + "/api/db/read", json=data)
    
    if code.status_code != 400:
        return make_response("Voter already exists", 400)
    
    # Voter does not exist is database. Insert his details in the database
    if(voter_id and voter_name and voter_dob):
        voter_secretkey = ''.join(random.choices(string.ascii_letters + string.digits + "-_", k = 8))

        data_insert = {
            "operation": "INSERT",
            "tablename": "voters",
            "columns": ["voter_id", "voter_name", "voter_dob", "voter_secretkey"],
            "values": [voter_id, voter_name, voter_dob, voter_secretkey]
        }

        requests.post(db_ip + "/api/db/modify", json=data_insert)

        return render_template("displaycode.html", voter_id = voter_id, voter_name = voter_name, voter_dob = voter_dob, voter_secretkey = voter_secretkey)
    
    # Unexpected error occurs
    return make_response("Error", 400)

@webserver.route("/adminlogin", methods=["GET"])
# API to handle the requests for the admin login page
def requestAdminLoginPage():
    return render_template("adminlogin.html")

@webserver.route("/api/admin/login", methods=["POST"])
# API to authenticate the admin
def loginAdmin(admin_id = None, admin_masterpwd = None):
    # Get admin details
    params = request.get_json()
    admin_id = params["admin_id"]
    admin_masterpwd = params["admin_masterpwd"]
    
    # Check with the admin dictionary
    if admin_id in details.keys():
        if admin_masterpwd == details[admin_id]:
            return make_response("Auth successful", 200)
    
    # Auth error
    return make_response("Auth Error", 400)

@webserver.route("/api/admin/ui", methods=["GET"])
# API to send admin page on successful authentication
def requestAdminUI(admin_id = None, admin_masterpwd = None):
    # Get admin context
    args = request.args
    admin_id = args["id"]
    admin_masterpwd = args["ctx"]

    # Check if the context is correct
    if admin_id in details.keys():
        if admin_masterpwd == details[admin_id]:
            return render_template("adminui.html", admin_id = admin_id)
    
    # Wrong context
    return make_response("Bad Request", 400)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@webserver.route("/api/election/create", methods=["POST"])
# API to initiate new elections
def createElection():
    pns = request.form.getlist("pn[]")
    rns = request.form.getlist("rn[]")
    pps = []
    rps = []
    
    for ele in request.files.getlist("pp[]"):
        if allowed_file(ele.filename):
            filename = secure_filename(ele.filename)
            file_blob = gcs_bucket.blob(filename)
            file_blob.upload_from_string(ele.read(), content_type=ele.content_type)
            pps.append(filename)
    
    for ele in request.files.getlist("rp[]"):
        if allowed_file(ele.filename):
            filename = secure_filename(ele.filename)
            file_blob = gcs_bucket.blob(filename)
            file_blob.upload_from_string(ele.read(), content_type=ele.content_type)
            rps.append(filename)

    election_data = set(zip(pns, pps, rns, rps))

    for pn, pp, rn, rp in election_data:
        data = {
            "operation": "INSERT",
            "tablename": "votingperiod",
            "columns": ["party_name", "party_photo", "rep_name", "rep_photo"],
            "values": [pn, pp, rn, rp]
        }

        requests.post(db_ip + "/api/db/modify", json=data)
    
    return make_response("Success!", 200)

@webserver.route("/api/election/complete", methods=["GET"])
# API to fetch election results
def completeElection():
    
    # ------------------------
    #           TODO
    # ------------------------
    
    # Once results of election is given, clear all the databases
    requests.post(db_ip + "/api/db/clear")

    return make_response("", 200)

# ---------------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    webserver.run(debug=True, port=port, host=host, use_reloader=False)
