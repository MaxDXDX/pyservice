"""The microservice manager."""

import os
import sys
import uuid
from datetime import datetime as dt
import time
import logging
from pathlib import Path

import celery.exceptions
from celery import Celery
from celery.result import AsyncResult
from pytz import timezone
import pika

from tgs_client import TgServiceClient

from pyservice.pyconfig.pyconfig import (
    AppConfig,
    MicroserviceConfig,
    BackuperConfig,
    DjangoBasedMicroserviceConfig
)
from pyservice.pyconfig.pyconfig import default_app_config
from pyservice.tcpwait.tcpwait import wait_for_tcp_service
from pyservice.files import files
from pyservice.files.files import create_if_not_yet
from pyservice.domain.cluster import Microservice, Backuper, deserialize_microservice
from pyservice.log_tools import log_tools


class AppManager:
    """Manager for arbitrary python app."""

    config: AppConfig
    _origin_file: Path
    test_mode: bool = False

    def __init__(self, config_of_service: AppConfig, origin_file: str | Path):
        self._origin_file = Path(origin_file)
        self.config = config_of_service

        self.set_root_logger()
        self.override_handlers_for_logger()

        self.log = self.get_manager_logger()
        self.post_app_manager_init()

    def post_app_manager_init(self):
        self.log_summary()

    def enable_test_mode(self):
        """For running tests."""
        self.test_mode = True

    def get_manager_logger(self):
        logger_name = f'{self.app_ref}-manager'
        log = log_tools.get_logger(
            log_name=logger_name,
            directory_for_logs=self.directory_for_logs,
            erase=self.config.delete_logs_on_start,
        )
        return log


    def set_root_logger(self):
        root_log = log_tools.get_logger(
            log_name='root',
            directory_for_logs=self.directory_for_logs,
            erase=self.config.delete_logs_on_start,
        )
        log_tools.remove_all_stream_handlers(logger=root_log)


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
    def directory_for_tests(self) -> Path:
        # pylint: disable=W0612
        parent_for_app_dir, app_dir, app_root_module = (
            self.base_project_directories)
        return app_dir / 'tests'

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

    def localed_dt(self, original: dt):
        try:
            return original.astimezone(tz=self.timezone)
        except AttributeError:
            return original

    def create_text_file_in_tmp_directory(
            self, content: str = None, filename: str = None) -> Path:
        return files.create_text_file_in_directory(
            self.directory_for_tmp, content, filename
        )

    def erase_tmp_directory(self):
        files.erase_directory(self.directory_for_tmp)
        detailed_tmp = files.DetailedDirectory(
            directory=self.directory_for_tmp)
        if detailed_tmp.entities.total_size_in_bytes > 0:
            raise RuntimeError('Tmp directory is not empty')

    def erase_logs_directory(self):
        # files.erase_directory(self.directory_for_logs)
        files.clear_all_files_in_directory(self.directory_for_logs)

    def get_logger_for_pyfile(
            self,
            pyfile: str | Path,
            with_path: bool = False,
    ) -> logging.Logger:
        logger = log_tools.get_logger_for_pyfile(
            pyfile=pyfile,
            directory_for_logs=self.directory_for_logs,
            with_path=with_path,
            erase=self.config.delete_logs_on_start,
        )
        return logger

    def override_handlers_for_logger(self) -> None:
        for _ in self.config.tracked_loggers:
            log_tools.get_logger(
                log_name=_,
                directory_for_logs=self.directory_for_logs,
                erase=self.config.delete_logs_on_start,
            )

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

    def log_summary(self):
        self.log.debug('Manager summary:')
        self.log.debug('=========== config ============')
        self.log.debug('- config: %s', self.config.as_yaml())
        self.log.debug('===============================')
        self.log.debug('sys.path: %s', sys.path)
        self.log.debug('- is app in test mode: %s',
                       self.test_mode)
        self.log.debug('- parent directory for app: %s',
                       self.directory_for_place_app_directory)
        self.log.debug('- directory for app: %s',
                       self.directory_for_app)
        self.log.debug('- directory for root module: %s',
                       self.root_module)
        self.log.debug('- directory for all data: %s',
                       self.directory_for_data)
        self.log.debug('- directory for temp files: %s',
                       self.directory_for_tmp)
        self.log.debug('- directory for logs: %s',
                       self.directory_for_logs)

    def on_start(self):
        print('performing <on start> operations...')
        self.log.debug('performing <on start> operations...')
        if self.config.delete_logs_on_start:
            self.erase_logs_directory()
            self.log.debug('logs directory has been erased!')


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
        self.init_celery_app()
        self.post_microservice_manager_init()

    def post_app_manager_init(self):
        pass

    def post_microservice_manager_init(self):
        super().post_app_manager_init()

    def enable_test_mode(self):
        """For running tests."""
        super().enable_test_mode()
        self.config.tg_group_for_system_notifications = (
            self.config.tg_group_for_tests)

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

    async def check_connection_to_telegram_server(self):
        url = self.config.tgs_server_url
        self.log.info('check TCP connection to Telegram Server (%s)', url)
        await wait_for_tcp_service(url)
        self.log.info('OK - Telegram Server on wire!')

    async def preflight_checks(self):
        self.log.info('performing preflight checks for microservice %s',
                      self.microservice.ref)
        await self.check_connection_to_telegram_server()
        await self.check_connection_to_rabbit_mq()
        self.test_rabbit_by_pika()

        self.send_message_to_telegram_chat(
            text=f'Preflight check for {self.microservice}',
            chat_id=self.config.tg_group_for_tests
        )

    def add_task_to_celery_scheduler(
            self,
            ref: str,
            schedule,
            task_name: str,
            args: tuple | dict = None,
    ):
        self.log.debug('adding task to celery scheduler...')
        scheduler: dict = self.celery_app.conf.beat_schedule
        scheduler[ref] = {
            'task': f'{self.app_ref}.{task_name}',
            'args': args,
            'schedule': schedule,
            'options': {'queue': self.microservice.own_queue},
        }
        self.log.debug('task added, current tasks: %s',
                       self.celery_app.conf.beat_schedule)

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
                              self.microservice.ref)

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
                    'options': {'queue': self.microservice.own_queue},
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

    def pre_init_celery_app(self):
        pass

    def init_celery_app(self) -> Celery:
        self.pre_init_celery_app()
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
                timeout=20,
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

    # pylint:disable=R0917
    def execute_celery_task(
            self,
            task_name: str,
            task_args: tuple = None,
            queue: str = None,
            wait_result: bool = True,
            timeout: int = None,
    ) -> dict:
        self.log.debug('executing celery task:')
        self.log.debug('- task name: %s', task_name)
        self.log.debug('- task args: %s', task_args)
        self.log.debug('- queue: %s', queue)
        self.log.debug('- need to wait result: %s', wait_result)
        self.log.debug('- timout: %s', timeout)
        if not queue:
            queue = self.microservice.ref
            self.log.debug('queue is not provided, '
                           'own queue will be used - %s', queue)
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

    def on_start(self):
        super().on_start()
        self.system_notification(f'{self.microservice} has been started!')

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

    def log_summary(self):
        super().log_summary()
        self.log.debug('- celery app: %s', self.celery_app)
        self.log.debug('- microservice: %s', self.microservice)
        self.log.debug('- celery config: %s',
                       self.celery_app.conf)

    def send_message_to_telegram_chat(self, text, chat_id):
        self.log.debug('sending text to the chat with id="%s"', chat_id)
        tg_client = TgServiceClient(
            url=self.config.tgs_server_url,
        )
        sender_phone = self.config.tg_account_for_sending_notifications
        tg_chat = chat_id
        sent_message = tg_client.send_text_message(
            app_phone=str(sender_phone),
            receiver=tg_chat,
            text=text[:4000]
        )
        assert isinstance(sent_message, dict)
        self.log.debug('message has been sent successfully: %s', sent_message)

    def system_notification(self, text):
        header = f'Notification from "{self.microservice.ref}":\n'
        text = header + text
        tg_chat = self.config.tg_group_for_system_notifications
        self.send_message_to_telegram_chat(text, chat_id=tg_chat)


class DjangoBasedMicroserviceManager(MicroServiceManager):
    """Manager for microservice powered by Django."""

    config: DjangoBasedMicroserviceConfig

    def pre_init_celery_app(self):
        self.set_django_setting_module_at_environment()

    def set_django_setting_module_at_environment(self):
        os.environ.setdefault(
            'DJANGO_SETTINGS_MODULE', self.django_settings_module)

    @property
    def django_directory(self) -> Path:
        result = self.root_module / 'django'
        assert result.is_dir()
        return result

    @property
    def django_main_app_directory(self) -> Path:
        django_dir = self.django_directory
        nested_dirs = files.get_list_of_directories_in_directory(
            directory=django_dir, mask='*'
        )
        for d in nested_dirs:
            pyfiles = files.get_list_of_files_in_directory(
                directory=d, mask='*.py'
            )
            filenames = [_.name for _ in pyfiles]
            if 'settings.py' in filenames:
                return d
        raise ValueError('Can not find directory with main django app.')

    @property
    def django_main_app_module(self) -> str:
        as_path = self.django_main_app_directory
        assert as_path.is_dir()
        from_src = str(as_path).partition('/src/')[2]
        as_module = from_src.replace('/', '.')
        return as_module

    @property
    def django_main_app_config_class(self) -> str:
        return f'{self.django_main_app_module}.apps.MainConfig'

    @property
    def django_root_urlconf(self) -> str:
        return f'{self.django_main_app_module}.urls'

    @property
    def django_main_app_module_name(self) -> str:
        return self.django_main_app_module.split('.', maxsplit=1)[-1]

    @property
    def django_settings_module(self) -> str:
        return f'{self.django_main_app_module}.settings'

    @property
    def gunicorn_config_file_path(self) -> Path:
        result = self.django_directory / 'gunicorn_config.py'
        assert result.is_file()
        return result

    @property
    def gunicorn_log_file_path(self) -> Path:
        result = self.directory_for_logs / 'gunicorn.log'
        return result

    @property
    def wsgi_app(self) -> str:
        'ma.django.tgbotapi.wsgi:application'
        return f'{self.django_main_app_module}.wsgi:application'

    @property
    def wsgi_app_with_only_dots(self) -> str:
        'ma.django.tgbotapi.wsgi.application'
        return self.wsgi_app.replace(':', '.')

    @property
    @create_if_not_yet
    def web_static_files_directory(self) -> Path:
        result = self.artefacts_directory / 'static'
        return result

    @property
    def is_django_test_mode(self) -> bool:
        """Whether django test has been started or not."""
        return sys.argv[1:2] == ['test']

    @property
    def django_db_settings(self) -> dict:
        if not self.is_django_test_mode:
            result = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': self.config.django_db_name,
                'USER': self.config.django_db_user,
                'PASSWORD': self.config.django_db_password,
                'HOST': self.config.django_db_hostname,
                'PORT': self.config.django_db_port,
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
            }
        else:
            result = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': self.django_directory / 'db.sql',
            }
        return result

    def erase_web_static_files_directory(self):
        files.erase_directory(self.web_static_files_directory)
        self.log.debug('directory with web static files erased')

    def on_start(self):
        super().on_start()
        self.erase_web_static_files_directory()

    async def preflight_checks(self):
        await super().preflight_checks()
        assert self.django_directory.is_dir()
        await self.check_connection_to_db()
        if self.config.is_keycloak_auth_enabled:
            await self.check_connection_to_keycloak()

    async def check_connection_to_db(self):
        hostname = self.config.django_db_hostname
        port = self.config.django_db_port
        self.log.info('checking TCP connection to django`s database (%s:%s)',
                      hostname, port)
        await wait_for_tcp_service(
            (hostname, port)
        )
        self.log.info('OK - django`s database on wire!')

    async def check_connection_to_keycloak(self):
        self.log.info('checking TCP connection to keycloak at %s',
                      self.config.keycloak_url)
        await wait_for_tcp_service(self.config.keycloak_url)
        self.log.info('OK - keycloak on wire!')

    def log_summary(self):
        super().log_summary()
        self.log.debug('- directory for django: %s',
                       self.django_directory)
        self.log.debug('- directory with django main app: %s',
                       self.django_main_app_directory)
        self.log.debug('- django main app module: %s',
                       self.django_main_app_module)
        self.log.debug('- django main app module config class: %s',
                       self.django_main_app_config_class)
        self.log.debug('- django main app module name: %s',
                       self.django_main_app_module_name)
        self.log.debug('- django settings module: %s',
                       self.django_settings_module)
        self.log.debug('- django root urlconf: %s',
                       self.django_root_urlconf)
        self.log.debug('- directory for django web static files: %s',
                       self.web_static_files_directory)
        self.log.debug('- gunicorn config file path: %s',
                       self.gunicorn_config_file_path)
        self.log.debug('- wsgi application '
                       '(with colon - for gunicorn config): %s',
                       self.wsgi_app)
        self.log.debug('- wsgi application '
                       '(with only dots - for django`s settings): %s',
                       self.wsgi_app_with_only_dots)
        self.log.debug('- is django test mode: %s',
                       self.is_django_test_mode)
        self.log.debug('- database settings: %s',
                       self.django_db_settings)


default_app_manager = AppManager(default_app_config, __file__)


def get_default_app_manager():
    return AppManager(default_app_config, __file__)
