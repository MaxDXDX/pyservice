"""Tasks for celery."""

import logging

from celery.utils.log import get_task_logger
from calculator import manager, config


log = get_task_logger('celery_tasks')
log.addHandler(
    logging.FileHandler(manager.directory_for_logs / 'celery_tasks.log'))


@manager.celery_app.task
def on_celery_start():
    manager.write_celery_test_file_2()  # do not delete this operation


@manager.celery_app.task
def sum_two_numbers(a: int, b: int):
    return round(a + b, int(config.round_to))


@manager.celery_app.task
def multiply_two_numbers(a: int, b: int):
    return round(a * b, int(config.round_to))
