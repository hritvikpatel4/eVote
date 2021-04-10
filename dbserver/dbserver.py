# ---------------------------------------- IMPORT HERE ----------------------------------------

from flask import Flask, jsonify, make_response, request
from sqlite3 import connect
import os, requests

# ---------------------------------------- CONFIGS ----------------------------------------

dbserver = Flask(__name__)
host = "0.0.0.0"
dbfile = "evote.db"
counter_db = "counter.db"
db_ip = "0.0.0.0"

# ---------------------------------------- MISC HANDLER FUNCTIONS ----------------------------------------

# Handler function to construct queries from the data sent from the webserver
def construct_query(data):
	# data is of JSON type
	
    # INSERT operation
	if data["operation"] == "INSERT":
		SQLQuery = "INSERT INTO {} ({}".format(data["tablename"], data["columns"][0])
		for value in range(1, len(data["columns"])):
			SQLQuery += ",{}".format(data["columns"][value])
		SQLQuery += ") VALUES ('{}'".format(data["values"][0])
		for value in range(1, len(data["values"])):
			SQLQuery += ",'{}'".format(data["values"][value])
		SQLQuery += ");"
	
	# SELECT operation
	elif data["operation"] == "SELECT":
		if data["columns"] == "*":
			SQLQuery = "SELECT *"
		else: 
			SQLQuery = "SELECT {}".format(data["columns"][0])
			for value in range(1, len(data["columns"])):
				SQLQuery += ",{}".format(data["columns"][value])
		SQLQuery += " FROM {} WHERE {}".format(data["tablename"], data["where"][0])
		for value in range(1, len(data["where"])):
			SQLQuery += "AND {}".format(data["where"][value])
		SQLQuery += ";"

	# DELETE operation
	elif data["operation"] == "DELETE":
		SQLQuery = "DELETE FROM {}".format(data["tablename"])
		if "where" in data.keys():
			SQLQuery += " WHERE "
			for condition in data["where"]:
				SQLQuery += condition
		SQLQuery += ";"

	# UPDATE operation
	elif data["operation"] == "UPDATE":
		SQLQuery = "UPDATE {} SET {} = {} + {}".format(data["tablename"], data["column"], data["column"], data["update_value"])
		if "where" in data.keys():
			SQLQuery += " WHERE {}".format(data["where"])
		SQLQuery += ";"

	return SQLQuery

# Handler function to connect to sqlite3 database
def connectDB(db):
    conn = None

    try:
        conn = connect(db)
    
    except:
        print("Error connecting to database")
    
    return conn

# ---------------------------------------- DATABASE ENDPOINTS ----------------------------------------

@dbserver.route("/api/db/generateBatchID", methods=["GET"])
# API which returns the batch id to the requester
def generateBatchID():
    conn = connectDB(counter_db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM counter;")
    batch_id = cursor.fetchone()[0]
    conn.commit()

    cursor.execute("UPDATE counter SET batch_id = batch_id + 1;")
    conn.commit()
    cursor.close()
    conn.close()

    resp = {
        "batchid": batch_id
    }
    
    return make_response(resp, 200)

@dbserver.route("/api/db/read", methods=["POST"])
# API to read from the database
def readDB():
    data = request.get_json()
    query = construct_query(data)

    conn = connectDB(dbfile)
    cursor = conn.cursor()

    cursor.execute(query)
    rows = []
    for i in cursor.fetchall():
        rows.append(i)
    
    cursor.close()
    conn.close()

    if not rows:
        return make_response("", 400)

    return jsonify(rows), 200

@dbserver.route("/api/db/modify", methods=["POST"])
# API to either insert or update data in the database
def modifyDB():
    data = request.get_json()
    query = construct_query(data)

    conn = connectDB(dbfile)
    cursor = conn.cursor()
    
    cursor.execute(query)
    conn.commit()
    
    cursor.close()
    conn.close()

    return "", 200

@dbserver.route("/api/db/clear", methods=["POST"])
# API to clear the databases
def clearDB():
    data1 = {
        "operation": "DELETE",
        "tablename": "votingperiod",
        "where": ["1=1"]
    }

    data2 = {
        "operation": "DELETE",
        "tablename": "voters",
        "where": ["1=1"]
    }

    try:
        requests.post("http://" + db_ip + ":80" + "/api/db/modify", json = data1)
        requests.post("http://" + db_ip + ":80" + "/api/db/modify", json = data2)

        conn = connectDB(counter_db)
        cursor = conn.cursor()
        cursor.execute("UPDATE counter SET batch_id = 1;")
        conn.commit()
        cursor.close()
        conn.close()
        
        return make_response("", 200)
    
    except:
        return make_response("Bad Request", 400)

# ---------------------------------------- MAIN ----------------------------------------

def main():
    return dbserver

if __name__ == '__main__':
    main()

application = main()
