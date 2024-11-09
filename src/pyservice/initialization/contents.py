"""Templates."""


microservice_config = """# from pydantic import ()

from pyservice.pyconfig.pyconfig import MicroserviceConfig


class Config(MicroserviceConfig):
    pass


config = Config()
"""


microservice_init = """
from celery.signals import worker_ready

from .config import config
from pyservice.manager.manager import MicroServiceManager

manager = MicroServiceManager(config, __file__)
celery_app = manager.celery_app


@worker_ready.connect
def at_start(sender, **k):
    manager.on_celery_worker_ready(sender)
"""

gitignore = """
venv/
__pycache__/
.idea

dist
build
restart-celery.sh
**egg-info
artefacts
"""

celery_tasks = """
import logging
from logging import Formatter, FileHandler

from celery.utils.log import get_task_logger
from celery.schedules import crontab

from {{ app_name }} import manager, config

log = get_task_logger('celery_tasks')
formatter = Formatter(
    '%(asctime)s %(name)-20s - %(levelname)-5s - %(message)s'
)
fh = logging.FileHandler(manager.directory_for_logs / 'celery_tasks.log')
fh.setFormatter(formatter)
log.addHandler(fh)

log.info('Logger for celery tasks: %s', log)


# manager.add_task_to_celery_scheduler(
#     ref='some-task',
#     schedule=crontab(minute='40'),
#     task_name='my-task',
# )

@manager.celery_app.task
def on_celery_start():
    manager.write_celery_test_file_2()  # do not delete this operation
    log.debug('celery`s on-start test passed!')

"""