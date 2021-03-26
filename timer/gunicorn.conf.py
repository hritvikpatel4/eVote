import multiprocessing, os

bind = "0.0.0.0:{}".format(os.environ["CUSTOM_PORT"])
workers = 1
threads = 1
