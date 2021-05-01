import multiprocessing, os

bind = "0.0.0.0:{}".format(os.environ["CUSTOM_PORT"])
worker_class = "gevent"
workers = 1
threads = multiprocessing.cpu_count() * 3 + 1
keepalive = 60
