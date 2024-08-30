"""The microservice manager."""


import asyncio
import uuid
from datetime import datetime as dt
import time
import logging
from pathlib import Path

import celery.exceptions
from pytz import timezone
import pika

from pyservice.pyconfig.pyconfig import (
    AppConfig, MicroserviceConfig, BackuperConfig)
from pyservice.pyconfig.pyconfig import default_app_config
from pyservice.tcpwait.tcpwait import wait_for_tcp_service
from pyservice.files import files
from pyservice.files.files import create_if_not_yet
from pyservice.domain.cluster import Microservice, Backuper, deserialize_microservice


from celery import Celery
from celery.result import AsyncResult


class AppManager:
    """Manager for arbitrary python app."""

    config: AppConfig
    _origin_file: Path

    def __init__(self, config_of_service: AppConfig, origin_file: str | Path):
        self._origin_file = Path(origin_file)
        self.config = config_of_service
        self.log = logging.getLogger(self.app_ref)
        self.log.setLevel(logging.DEBUG)
        fh = logging.FileHandler(
            self.directory_for_logs /
            f'{self.app_ref}-manager.log')
        self.log.addHandler(fh)
        self.log.debug('--------------------------------------------------')
        self.log.debug('%s manager initiated at %s', self.app_ref, dt.now())

    @property
    def directory_for_place_app_directory(self):
        # pylint: disable=W0612
        parent_for_app_dir, app_dir, app_root_module = (
            self.base_project_directories)
        return parent_for_app_dir

    @property
    def directory_for_app(self) -> Path:
        # pylint: disable=W0612
        parent_for_app_dir, app_dir, app_root_module = (
            self.base_project_directories)
        return app_dir

    @property
    def root_module(self) -> Path | None:
        # pylint: disable=W0612
        parent_for_app_dir, app_dir, app_root_module = (
            self.base_project_directories)
        return app_root_module

    @property
    def root_module_name(self) -> str:
        root_module = self.root_module
        if root_module:
            return root_module.name
        raise ValueError('Can not get name of root module')

    @property
    def app_ref(self) -> str:
        return self.root_module.name if self.root_module else 'unknown'

    @property
    def base_project_directories(self) -> tuple[Path, Path, Path]:
        """Detect:
        - the parent for app directory
        - app directory
        - root module of app (the first after <src> directory)
        """
        root_module = None

        config_location = self._origin_file
        current_dir = config_location.parent
        previous_dir = None
        while True:
            if current_dir.name == 'src':
                root_module = previous_dir
            dirs = files.get_list_of_directories_in_directory(
                current_dir, mask='*')
            for directory in dirs:
                if directory.name in ['src', 'tests', 'test']:
                    app_dir = directory.parent
                    parent_for_app_dir = app_dir.parent
                    return parent_for_app_dir, app_dir, root_module
                elif directory.name == '/':
                    raise ValueError(
                        'Can not detect project dir and its parent!')
            previous_dir = current_dir
            current_dir = current_dir.parent

    @property
    @create_if_not_yet
    def artefacts_directory(self) -> Path:
        return self.directory_for_app / 'artefacts'

    @property
    @create_if_not_yet
    def directory_for_tmp(self) -> Path:
        return self.artefacts_directory / 'tmp'

    @property
    @create_if_not_yet
    def directory_for_logs(self) -> Path:
        return self.artefacts_directory / 'logs'

    @property
    @create_if_not_yet
    def directory_for_data(self) -> Path:
        return self.artefacts_directory / 'data'

    @property
    def timezone(self):
        return timezone(self.config.tz)

    def get_now(self, human_readable: bool = False) -> dt:
        now = dt.now(tz=self.timezone)
        if not human_readable:
            return now
        else:
            dt_format = '%d.%m.%y %H:%M (%Z)'
            as_text = now.strftime(dt_format)
            return as_text

    def create_text_file_in_tmp_directory(
            self, content: str = None, filename: str = None) -> Path:
        return files.create_text_file_in_directory(
            self.directory_for_tmp, content, filename
        )

    def erase_tmp_directory(self):
        files.erase_directory(self.directory_for_tmp)
        detailed_tmp = files.DetailedDirectory(self.directory_for_tmp)
        if detailed_tmp.entities.total_size_in_bytes > 0:
            raise RuntimeError('Tmp directory is not empty')

    def get_logger_for_pyfile(self, pyfile: str | Path) -> logging.Logger:
        pyfile = Path(pyfile)
        stem = pyfile.stem
        log = logging.getLogger(stem)
        file_handler = logging.FileHandler(self.directory_for_logs /
                                           f'{stem}.log')
        formatter = logging.Formatter(
            '%(asctime)s %(name)-10s - %(levelname)-5s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel('DEBUG')
        log.addHandler(file_handler)
        log.setLevel('DEBUG')
        log.debug('Logger for %s: %s', pyfile, log)
        return log

    def print_summary(self):
        return (
            f'App summary:\n'
            f'Directories:\n'
            f'- app parent: {self.directory_for_place_app_directory}\n'
            f'- app: {self.directory_for_app}\n'
            f'- tmp: {self.directory_for_tmp}\n'
            f'- data: {self.directory_for_data}\n'
            f'- logs: {self.directory_for_logs}\n'
            f'Root module (app ref): {self.app_ref}\n'
        )

    def on_start(self):
        print('performing <on start> operations...')
        self.log.debug('performing <on start> operations...')
        ## TODO: logger stops write logs after removing files!
        # if self.config.delete_logs_on_start:
        #     current_logs = files.get_list_of_files_in_directory(
        #         self.directory_for_logs)
        #     files.erase_directory(self.directory_for_logs)
        #     print('all logs in directory %s have been deleted: %s',
        #           self.directory_for_logs, current_logs)
        self.log.debug('<on start> operations executed!')
        self.log.info('app %s started!', self.app_ref)
        print('performing <on start> operations...')


class MicroServiceManager(AppManager):
    """The manager for microservice."""

    config: MicroserviceConfig
    celery_app: Celery = None

    microservice: Microservice

    def __init__(
            self,
            config_of_microservice: MicroserviceConfig,
            *args, **kwargs
    ):
        super().__init__(config_of_microservice, *args, **kwargs)
        asyncio.run(self.preflight_checks())
        self.init_celery_app()

    @property
    def celery_test_file(self):
        return (self.directory_for_tmp /
                'celery_test_file')

    @property
    def celery_test_file_2(self):
        return (self.directory_for_tmp /
                'on-celery-start-handler-is-ready')

    def write_celery_test_file(self):
        self.log.warning('creating test file for celery - %s',
                         self.celery_test_file)
        now = dt.now()
        self.celery_test_file.unlink(missing_ok=True)
        with open(self.celery_test_file, 'w', encoding='utf-8') as f:
            f.write(f'this is a test file!\n'
                    f'Created at: {now.isoformat()}\n')
        return self.celery_test_file

    def write_celery_test_file_2(self):
        test_file = self.celery_test_file_2
        now = dt.now()
        self.celery_test_file.unlink(missing_ok=True)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(f'this is a test file!\n'
                    f'Created at: {now.isoformat()}\n')
        return test_file

    def check_celery_test_files(self):
        duration = self.config.time_to_wait_celery_test_file
        is_passed = False
        current_attempt = 0
        print(f'checking celery test files (time limit - {duration}) ...')
        while not is_passed:
            print(f'current attempt - {current_attempt}/{duration} ...')
            test_files = [
                self.celery_test_file,
                self.celery_test_file_2,
            ]
            is_passed = True
            for test_file in test_files:
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        assert 'this is a test file!' in content

                    with open(test_file, 'a', encoding='utf-8') as f:
                        msg = f'\ncheck passed at {dt.now().isoformat()}'
                        f.write(msg)
                except FileNotFoundError:
                    is_passed = False
                else:
                    is_passed = is_passed and True

            if not is_passed:
                if current_attempt > duration:
                    raise RuntimeError('Celery is not working!')
                else:
                    time.sleep(1)
                    current_attempt += 1

        print('All good! Celery is working fine!')

    @property
    def microservice(self) -> Microservice:
        ref = f'{self.app_ref}:{self.config.instance_tag}'
        queues = [
            ref,
            self.app_ref,
            self.config.default_celery_queue,
        ]
        if isinstance(self.config, BackuperConfig):
            klass = Backuper
        else:
            klass = Microservice
        m = klass(
            config=self.config,
            ref=ref,
            queues=queues,
            own_queue=ref,
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
        self.log.debug('getting celery app...')
        try:
            schedule_file = self.directory_for_tmp / 'celery-beat-schedule'
            manager = self

            class CeleryForMicroservice(Celery):
                # pylint: disable=W0613
                def gen_task_name(self, name, module):
                    return f'{manager.app_ref}.{name}'

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
                    f'{self.app_ref}.celery_tasks.tasks',
                ),
                beat_schedule_filename=schedule_file,
                task_default_queue=self.config.default_celery_queue,
            )

            @app.task
            def self_check():
                # TODO: add checks
                self.log.info('Selfcheck for service %s has been passed',
                              self.app_ref)

            @app.task
            def create_test_file():
                self.write_celery_test_file()

            # arg 'name' is used to bypass adding app prefix
            # to task_name (this is a global task)
            @app.task(name='service_info', time_limit=10)
            def service_info(publisher):
                self.log.debug('<%s> have been requested '
                               'service_info', publisher)
                result = self.microservice.as_dict()
                return result

            app.conf.beat_schedule = {
                'periodic-selfscheck': {
                    'task': f'{self.app_ref}.self_check',
                    'schedule': 5.0,
                },
            }

        except Exception as e:
            self.log.exception('Error during initializing celery app!')
            raise e
        else:
            self.log.debug('celery app initialized successfully')
            return app

    def on_celery_worker_ready(self, sender):
        with sender.app.connection() as conn:
            sender.app.send_task(
                f'{self.app_ref}.create_test_file',
                # create_test_file,
                connection=conn,
                queue=self.microservice.own_queue,
            )
            sender.app.send_task(
                f'{self.app_ref}.on_celery_start',
                connection=conn,
                queue=self.microservice.own_queue,
            )

    def init_celery_app(self) -> Celery:

        if not self.celery_app:
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

    def get_microservice_from_cluster(
            self, queue: str = None) -> Microservice | Backuper | None:
        queue = queue if queue else self.config.default_celery_queue
        self.log.debug('try to get microservice from cluster '
                       'by queue "%s"', queue)
        try:
            serialized = self.execute_celery_task(
                task_name='service_info',
                task_args=(self.microservice.ref, ),
                queue=queue,
                timeout=3,
            )
        except celery.exceptions.TimeoutError:
            logging.warning('can not find microservice with queue %s', queue)
            return None
        self.log.debug('found microservice: %s', serialized)
        microservice = deserialize_microservice(serialized)
        return microservice

    def get_my_microservice_from_cluster(self):
        return self.get_microservice_from_cluster(
            queue=self.microservice.own_queue
        )

    def get_all_cluster_microservices(self) -> set[Microservice]:
        result = set()
        first = self.get_microservice_from_cluster()
        result.add(first)
        next_one = None
        while next_one != first:
            next_one = self.get_microservice_from_cluster()
            result.add(next_one)
        return result

    def execute_celery_task(
            self,
            task_name: str,
            task_args: tuple = None,
            queue: str = None,
            wait_result: bool = True,
            timeout: int = None,
    ) -> dict:
        if not queue:
            queue = self.microservice.ref
        print(f'sending task <{task_name}> (args - {task_args}) '
              f'to queue <{queue}> '
              f'(wait result: {wait_result})...')
        result: AsyncResult = self.celery_app.send_task(
            task_name,
            queue=queue,
            args=task_args,
        )
        if wait_result:
            r = result.get(timeout=timeout)
            return r

        # app.conf.beat_schedule = {
        #     'execute_backup_routine': {
        #         'task': 'backuper.celery.tasks.execute_backup_routine',
        #         'schedule': crontab(hour=str(config.everyday_backup_hour),
        #                             minute=str(config.everyday_backup_min)),
        #     },
        # }

    def _get_connection_to_rabbitmq(self):
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config.rabbitmq_hostname,
                port=int(self.config.rabbitmq_port),
                virtual_host=self.config.rabbitmq_vhost,
                credentials=pika.PlainCredentials(
                    username=self.config.rabbitmq_username,
                    password=self.config.rabbitmq_password,
                )
            )
        )

    def test_rabbit_by_pika(self):
        print('Checking RabbitMQ by test message...')
        test_message = f'test message {uuid.uuid4()}'
        test_queue = f'test-{self.microservice.own_queue}'
        connection = self._get_connection_to_rabbitmq()
        channel = connection.channel()
        channel.queue_delete(queue=test_queue)
        channel.queue_declare(queue=test_queue)
        channel.basic_publish(
            exchange='',
            routing_key=test_queue,
            body=test_message,
        )

        # pylint: disable=W0612
        method_frame, header_frame, body = channel.basic_get(
            queue=test_queue,
            auto_ack=True,
        )
        received = body.decode('utf-8')
        assert test_message == received
        channel.queue_delete(queue=test_queue)
        connection.close()
        print('RabbitMQ is working!')


default_app_manager = AppManager(default_app_config, __file__)


def get_default_app_manager():
    return AppManager(default_app_config, __file__)
