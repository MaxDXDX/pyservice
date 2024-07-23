"""The microservice manager."""


import asyncio
from datetime import datetime as dt
import time
import logging
from pathlib import Path
from pytz import timezone

from pyservice.pyconfig.pyconfig import AppConfig, MicroserviceConfig
from pyservice.tcpwait.tcpwait import wait_for_tcp_service
from pyservice.files import files
from pyservice.manager import domain


from celery import Celery
from celery.result import AsyncResult


class AppManager:
    """Manager for arbitrary python app."""

    config: AppConfig

    def __init__(self, config_of_service: AppConfig):
        self.config = config_of_service
        self.log = logging.getLogger(self.config.app_ref)
        self.log.setLevel(logging.DEBUG)
        fh = logging.FileHandler(
            self.config.directory_for_logs /
            f'{self.config.app_ref}-manager.log')
        self.log.addHandler(fh)
        self.log.debug('%s manager initiated at %s',
                       self.config.app_ref, dt.now())

    @property
    def timezone(self):
        return timezone(self.config.tz)

    def get_now(self) -> dt:
        return dt.now(tz=self.timezone)

    def create_text_file_in_tmp_directory(
            self, content: str = None, filename: str = None) -> Path:
        return files.create_text_file_in_directory(
            self.config.directory_for_tmp, content, filename
        )

    def erase_tmp_directory(self):
        files.erase_directory(self.config.directory_for_tmp)


class MicroServiceManager(AppManager):
    """The manager for microservice."""

    config: MicroserviceConfig
    celery_app: Celery = None

    microservice: domain.Microservice

    @property
    def celery_test_file(self):
        return self.config.directory_for_tmp / 'celery_test_file'

    def write_celery_test_file(self):
        self.log.warning('creating test file for celery - %s',
                         self.celery_test_file)
        now = dt.now()
        self.celery_test_file.unlink(missing_ok=True)
        with open(self.celery_test_file, 'w', encoding='utf-8') as f:
            f.write(f'this is a test file!\n'
                    f'Created at: {now.isoformat()}\n')
        return self.celery_test_file

    def check_celery_test_file(self):
        duration = self.config.time_to_wait_celery_test_file
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

    @property
    def microservice(self) -> domain.Microservice:
        ref = f'{self.config.app_ref}--{self.config.instance_tag}'
        queues = [
            ref,
            self.config.app_ref,
            self.config.default_celery_queue,
        ]
        m = domain.Microservice(
            config=self.config,
            ref=ref,
            queues=queues,
        )
        return m

    def all_queues(self, as_text: bool = False) -> list[str]:
        queues = self.microservice.queues
        if as_text:
            queues = ','.join(queues)
        return queues

    async def check_connection_to_rabbit_mq(self):
        rabbit_hostname = self.config.rabbitmq_hostname
        rabbit_port = self.config.rabbitmq_port
        self.log.info('check TCP connection to RabbitMQ (%s:%s)',
                      rabbit_hostname, rabbit_port)
        await wait_for_tcp_service(
            (rabbit_hostname, rabbit_port)
        )
        self.log.info('OK - RabbitMQ on wire!')

    async def preflight_checks(self):
        self.log.info('performing preflight checks for microservice %s',
                      self.microservice.ref)
        await self.check_connection_to_rabbit_mq()

    def get_celery_app(self) -> Celery:
        schedule_file = self.config.directory_for_tmp / 'celery-beat-schedule'
        cfg = self.config

        class CeleryForMicroservice(Celery):
            # pylint: disable=W0613
            def gen_task_name(self, name, module):
                return f'{cfg.root_module_name}.{name}'

        app = CeleryForMicroservice(self.microservice.ref)
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
            imports=(
                f'{self.config.root_module}.celery_tasks.tasks',
                f'{self.config.root_module}.celery_tasks.default',
            ),
            beat_schedule_filename=schedule_file,
            task_default_queue=self.config.default_celery_queue,
        )
        return app

    def init_celery_app(self) -> Celery:

        if not self.celery_app:
            # self.celery_test_file.unlink(missing_ok=True)
            self.celery_app = self.get_celery_app()

        return self.celery_app

    def ping_to_self(self):
        task_name = 'ping_pong'
        print(f'pinging by task  <{task_name}>...')
        result: AsyncResult = self.celery_app.send_task(
            task_name,
            args=(f'My time is {self.get_now().isoformat()}. '
                  f'And that your time?', ),
            queue=self.config.default_celery_queue,
        )
        r = result.get()
        print(f'got answer at {self.get_now().isoformat()}: ', r)
        return r

    def get_microservice_from_cluster(self, queue: str = None):
        result: AsyncResult = self.celery_app.send_task(
            'service_info',
            args=(self.config.ref, ),
            queue=queue if queue else self.config.default_celery_queue,
        )
        r = result.get()
        return r

    def get_all_cluster_microservices(self):
        pass
        current = None
        # while True:
        #     next_microservice_info = self.get_microservice_from_cluster()
        #     if current:

    # def ping_to_everybody(self):
    #     task_name = f'{self.config.root_module_name}.ping_pong'
    #     print(f'pinging by task  <{task_name}>...')
    #     result: AsyncResult = self.celery_app.send_task(
    #         task_name,
    #         args=(f'My time is {self.get_now().isoformat()}. '
    #               f'And that your time?', ),
    #         queue=self.config.service_ref,
    #     )
    #     r = result.get()
    #     print(f'got answer at {self.get_now().isoformat()}: ', r)
    #     return r

    def send_task(self,
                  task_name: str,
                  queue: str = None,
                  wait_result: bool = True,
                  ):
        if not queue:
            queue = self.config.ref
        print(f'sending task <{task_name}> to queue <{queue}> '
              f'(wait result: {wait_result})...')
        result: AsyncResult = self.celery_app.send_task(
            task_name,
            queue=queue,
        )
        print('RESULT type:', type(result))
        print('RESULT:', result)
        if wait_result:
            r = result.get()
            return r

        # app.conf.beat_schedule = {
        #     'execute_backup_routine': {
        #         'task': 'backuper.celery.tasks.execute_backup_routine',
        #         'schedule': crontab(hour=str(config.everyday_backup_hour),
        #                             minute=str(config.everyday_backup_min)),
        #     },
        # }
