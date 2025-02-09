from celery.schedules import crontab

from .. import manager

log = manager.get_logger_for_celery_tasks()

## You might add periodic tasks here:
# manager.add_task_to_celery_scheduler(
#     ref='some-task',
#     schedule=crontab(minute='40'),
#     task_name='my_task',
# )

# This task run after the Celery has been started:
# You might add any other operation inside
@manager.celery_app.task
def on_celery_start():
    manager.write_celery_test_file_2()  # do not delete this default operation
    # put any other operations here
    log.debug('celery`s on-start test passed!')


# @manager.celery_app.task
# def my_task():
#     your logic
