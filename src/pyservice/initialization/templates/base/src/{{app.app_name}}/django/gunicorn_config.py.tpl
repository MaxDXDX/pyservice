"""Gunicorn *development* config file"""
import multiprocessing
from {{ app.app_name }} import manager
# from ma import config as microservice_config

# Django WSGI application path in pattern MODULE_NAME:VARIABLE_NAME
# wsgi_app = "ma.django.tgbotapi.wsgi:application"
wsgi_app = manager.wsgi_app
print(f'starting gunicorn server for wsgi app "{wsgi_app}" ...')

# The granularity of Error log outputs
loglevel = "debug"

# The number of worker processes for handling requests
cores = multiprocessing.cpu_count()
workers = cores * 2 + 1
print(f'you have {cores} cores and number of workers is set to: {workers}')
print('see: https://docs.gunicorn.org/en/stable/design.html#how-many-workers '
      'for details')

# The socket to bind
bind = "0.0.0.0:8000"

# Restart workers when code changes (development only!)
# reload = True
reload = False

# Write access and error info to /var/log
accesslog = errorlog = str(manager.gunicorn_log_file_path)

# Redirect stdout/stderr to log file
capture_output = True

# PID file so you can easily fetch process ID
pidfile = "/gunicorn.pid"

# Daemonize the Gunicorn process (detach & enter background)
daemon = True
# daemon = False

timeout = 600

# Server Hooks
# on_starting = manager.on_server_start
