"""The basic app entities."""


from celery.signals import worker_ready

from .config import config
from pyservice.manager.manager import MicroServiceManager

manager = MicroServiceManager(config, __file__)
celery_app = manager.celery_app


@worker_ready.connect
# pylint: disable=W0613
def at_start(sender, **k):
    manager.on_celery_worker_ready(sender)
