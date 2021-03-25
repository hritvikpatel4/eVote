import multiprocessing, os

bind = "0.0.0.0:{}".format(os.environ["CUSTOM_PORT"])
workers = multiprocessing.cpu_count() * 2 + 1
threads = 1
