from celery.signals import worker_ready
from pathlib import Path

from pyservice.files.files import create_if_not_yet

from .config import config, Config
from pyservice.manager.manager import DjangoBasedMicroserviceManager


class Manager(DjangoBasedMicroserviceManager):
    config: Config

    # feel free to extend or override base class


manager = Manager(config, __file__)
celery_app = manager.celery_app


@worker_ready.connect
def at_start(sender, **k):
    manager.on_celery_worker_ready(sender)
