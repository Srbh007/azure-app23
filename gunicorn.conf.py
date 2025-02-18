import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 600
keepalive = 5
worker_class = "sync"
worker_connections = 1000
accesslog = "-"
errorlog = "-"