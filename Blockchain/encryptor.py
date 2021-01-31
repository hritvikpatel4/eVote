import os, time
from cryptography.fernet import Fernet
from datetime import datetime

def init():
    mykey = Fernet.generate_key()
    kf = open("secret.file", "wb")
    kf.write(mykey)
    kf.close()

def loadkey():
    return open("secret.file", "rb").read()

def encrypt(filename, mykey):
    fdr = open(filename, "rb")
    data = fdr.read()
    f = Fernet(mykey)
    enc_data = f.encrypt(data)
    fdw = open(filename, "wb")
    fdw.write(enc_data)
    fdr.close()
    fdw.close()
    os.sync()
    del f

def decrypt(filename, mykey):
    fdr = open(filename, "rb")
    data = fdr.read()
    f = Fernet(mykey)
    dec_data = f.decrypt(data)
    fdw = open(filename, "wb")
    fdw.write(dec_data)
    fdr.close()
    fdw.close()
    os.sync()
    del f

if __name__ == '__main__':
    init()

    csvfile = open("data.csv", "wb")
    csvfile.write(("key" + "," + "candidateVoted\n").encode())
    csvfile.close()
    os.sync()

    times = []

    encrypt("data.csv", loadkey())

    for i in range(100):
        st = time.time()
        decrypt("data.csv", loadkey())
        s = (str(i) + "," + "narendra_modi\n").encode()
        csvfile = open("data.csv", "ab+")
        csvfile.write(s)
        encrypt("data.csv", loadkey())
        et = time.time()

        times.append(et - st)
    
    # decrypt("data.csv", loadkey())

    timefile = open("exec_time.txt", "w")

    for x in times:
        timefile.write(str(x) + "\n")
    
    timefile.close()
    os.sync()

    print("DONE!")

'''
1. call encryptor -> gen prevKey and also encrypt the data
2. subsequent calls to encrypto -> keeps prevKey to decrypt data. use newKey to encrypt data after appending
'''