"""Tasks for celery."""

import logging
import random

from celery.utils.log import get_task_logger
from calculator import manager, config


log = get_task_logger('celery_tasks')
log.addHandler(
    logging.FileHandler(manager.directory_for_logs / 'celery_tasks.log'))

scheduler: dict = manager.celery_app.conf.beat_schedule

# adding periodic tasks (replace by yours or comment to switch off):
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
scheduler['daily-backup'] = {
    'task': f'{manager.app_ref}.minutely_calculation',
    'schedule': 5.0,
}

log.debug('Tasks in SCHEDULER: %s', scheduler)


@manager.celery_app.task
def on_celery_start():
    manager.write_celery_test_file_2()  # do not delete this operation


@manager.celery_app.task
def sum_two_numbers(a: int, b: int):
    return round(a + b, int(config.round_to))


@manager.celery_app.task
def multiply_two_numbers(a: int, b: int):
    return round(a * b, int(config.round_to))


@manager.celery_app.task
def minutely_calculation():
    log.debug('start next periodic calculation...')
    a = random.randint(1, 1000)
    b = random.randint(2, 1000)
    result = multiply_two_numbers(a, b)
    log.debug('result: %s * %s = %s', a, b, result)
    return result
