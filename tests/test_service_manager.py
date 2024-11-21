"""
Tests.
"""

from pathlib import Path

from unittest import IsolatedAsyncioTestCase, TestCase
from celery import Celery


from pyservice.pyconfig.pyconfig import default_microservice_config
from pyservice.manager.manager import get_default_microservice_manager
from pyservice.manager.manager import get_default_app_manager
from pyservice.domain import cluster


class MicroserviceDomainTestCase(TestCase):
    """Domain models."""

    def test_microservice(self):
        service = cluster.Microservice(ref='my-service')
        clone = cluster.Microservice(
            ref='my-service', config=default_microservice_config)
        self.assertEqual(service, clone)
        my_cluster: set[cluster.Microservice] = set()
        self.assertEqual(len(my_cluster), 0)
        my_cluster.add(service)
        self.assertEqual(len(my_cluster), 1)
        my_cluster.add(clone)
        self.assertEqual(len(my_cluster), 1)

    def test_backuper_model(self):
        backuper = cluster.Backuper(
            ref='test-backuper',
            config=cluster.BackuperConfig(),
        )
        serialized = backuper.as_dict()
        restored = cluster.deserialize_microservice(serialized)
        self.assertEqual(backuper, restored)


class MicroserviceManagerTestCase(IsolatedAsyncioTestCase):
    """Microservice manager test."""

    def setUp(self) -> None:

        self.mng = get_default_microservice_manager()
        assert self.mng.seq_params
        self.mng.enable_test_mode()

    async def test_check_connection_to_seq(self):
        is_ok = await self.mng.check_connection_to_seq()
        self.assertTrue(is_ok is True)

    async def test_check_connection_to_rabbit(self):
        await self.mng.check_connection_to_rabbit_mq()

    async def test_check_connection_to_telegram_server(self):
        await self.mng.check_connection_to_telegram_server()

    async def test_preflight_checks(self):
        await self.mng.preflight_checks()

    def test_get_celery_app(self):
        app = self.mng.get_celery_app()
        self.assertIsInstance(app, Celery)

    def test_base_directories(self) -> None:
        manager = get_default_app_manager()

        for attr in [
            'directory_for_app',
            'directory_for_place_app_directory',
            'root_module',
        ]:
            with self.subTest(attr=attr):
                path = getattr(manager, attr)
                self.assertIsInstance(path, Path)
                self.assertTrue(path.is_dir())

        # for config in tests folder (not in src)
        # TODO: detect root module for tests configs

    def test_artefacts_directories(self) -> None:
        data = self.mng.directory_for_data
        tmp = self.mng.directory_for_tmp
        logs = self.mng.directory_for_logs
        self.assertTrue(data.is_dir())
        self.assertTrue(tmp.is_dir())
        self.assertTrue(logs.is_dir())

    def test_test_rabbit_by_pika(self):
        self.mng.test_rabbit_by_pika()

    def test_get_all_microservices(self):
        all_microservices = self.mng.get_all_cluster_microservices()
        self.assertIsInstance(all_microservices, set)

    def test_get_microservice_bad_path(self):
        result = self.mng.get_microservice_from_cluster(
            queue='unreal-queue'
        )
        self.assertEqual(result, None)

    def test_get_logger(self):
        log = self.mng.get_logger_for_pyfile(__file__)

        def inner_func():
            log.debug('record from inner function')

        def my_func():
            log.debug('record from main function')
            inner_func()
            log.debug('another record from main function')

        my_func()

    def test_send_system_notification_to_telegram_chat(self):
        msg = 'TEST: system notification'
        self.mng.system_notification(msg)

    def test_get_installed_packages(self):
        installed_packages = self.mng.get_installed_packages()
        self.assertIsInstance(installed_packages, list)
        self.assertGreater(len(installed_packages), 0)

        is_pyservice_installed = self.mng.is_pyservice_installed()
        self.assertTrue(is_pyservice_installed is True)
