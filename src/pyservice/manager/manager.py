"""The microservice manager."""


import asyncio
from datetime import datetime as dt
import time

from pyservice.pyconfig.pyconfig import PyConfig, MicroserviceConfig
from pyservice.tcpwait.tcpwait import wait_for_tcp_service


from celery import Celery


class ServiceManager:
    config: PyConfig

    def __init__(self, config_of_service: PyConfig):
        self.config = config_of_service


class MicroServiceManager(ServiceManager):
    """The manager for microservice."""

    config: MicroserviceConfig
    celery_app: Celery = None

    @property
    def celery_test_file(self):
        return self.config.directory_for_tmp / 'celery_test_file'

    def write_celery_test_file(self):
        now = dt.now()
        with open(self.celery_test_file, 'w', encoding='utf-8') as f:
            f.write(f'this is a test file!\n'
                    f'Created at: {now.isoformat()}\n')

    def check_celery_test_file(self):
        duration = self.config.time_to_waiting_celery_test_file
        print(f'sleep {duration} seconds before check celery test file...')
        time.sleep(duration)
        print('checking celery test file...')
        try:
            with open(self.celery_test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'this is a test file!' in content

            with open(self.celery_test_file, 'a', encoding='utf-8') as f:
                msg = f'\ncheck passed at {dt.now().isoformat()}'
                content = f.write(msg)
        except FileNotFoundError as e:
            raise RuntimeError('Celery is not working!') from e

    def __init__(self, config_of_microservice: MicroserviceConfig):
        super().__init__(config_of_microservice)
        asyncio.run(self.preflight_checks())
        self.init_celery_app()

    async def check_connection_to_rabbit_mq(self):
        rabbit_hostname = self.config.rabbitmq_hostname
        rabbit_port = self.config.rabbitmq_port
        print(f'- checking connection to Rabbit MQ '
              f'({rabbit_hostname}:{rabbit_port}) ...')
        await wait_for_tcp_service(
            (rabbit_hostname, rabbit_port)
        )
        print('  rabbit on wire!')

    async def preflight_checks(self):
        print('Performing preflight checks for microserivce with config:')
        print(self.config)
        await self.check_connection_to_rabbit_mq()

    def get_celery_app(self) -> Celery:
        app = Celery(self.config.service_ref)
        broker_url = (f'amqp://'
                      f'{self.config.rabbitmq_username}:'
                      f'{self.config.rabbitmq_password}'
                      f'@{self.config.rabbitmq_hostname}:'
                      f'{self.config.rabbitmq_port}'
                      f'/{self.config.rabbitmq_vhost}')

        app.conf.update(
            enable_utc=True,
            timezone=str(self.config.tz),
            broker_url=broker_url,
            result_backend='rpc',
            imports=(f'{self.config.root_module_name}.celery_tasks.tasks',),
            beat_schedule_filename=self.config.directory_for_tmp /
                                   f'{self.config.root_module_name}'
                                   f'-celery-beat-schedule'
        )

        return app

    def init_celery_app(self) -> Celery:

        self.celery_test_file.unlink(missing_ok=True)

        if not self.celery_app:
            self.celery_app = self.get_celery_app()

        return self.celery_app

        # app.conf.beat_schedule = {
        #     'execute_backup_routine': {
        #         'task': 'backuper.celery.tasks.execute_backup_routine',
        #         'schedule': crontab(hour=str(config.everyday_backup_hour),
        #                             minute=str(config.everyday_backup_min)),
        #     },
        # }
