import multiprocessing
import os

# Server socket
bind = "0.0.0.0:3000"  # Listen on all interfaces
backlog = 2048

# Worker processes
workers = 1  # Reduced to 1 worker
worker_class = "gthread"
threads = 2
worker_connections = 1000
timeout = 30
keepalive = 2

# Process naming
proc_name = "chanclas_api"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Server hooks
def on_starting(server):
    """
    Log server start
    """
    server.log.info("Starting Chanclas API server")

def on_exit(server):
    """
    Log server exit
    """
    server.log.info("Stopping Chanclas API server")

def worker_int(worker):
    """
    Log worker interrupt
    """
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """
    Log worker abort
    """
    worker.log.info("Worker received SIGABRT signal")

# Memory management
max_requests = 500
max_requests_jitter = 50

def worker_exit(server, worker):
    """
    Clean up resources when worker exits
    """
    import gc
    gc.collect() 