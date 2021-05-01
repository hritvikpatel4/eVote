import multiprocessing, os

bind = "0.0.0.0:{}".format(os.environ["CUSTOM_PORT"])
worker_class = "gevent"
workers = 1
threads = multiprocessing.cpu_count() * 2 + 1
