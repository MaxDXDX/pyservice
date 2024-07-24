"""
Tests.
"""

from pathlib import Path

from unittest import IsolatedAsyncioTestCase, TestCase
from celery import Celery


from pyservice.pyconfig.pyconfig import MicroserviceConfig
from pyservice.pyconfig.pyconfig import default_microservice_config
from pyservice.manager.manager import MicroServiceManager
from pyservice.manager.manager import default_app_manager
from pyservice.domain import cluster


class MicroserviceDomainTestCase(TestCase):
    """Domain models."""

    def test_microservice(self):
        service = cluster.Microservice(ref='my-service')
        clone = cluster.Microservice(ref='my-service',
                               config=default_microservice_config)
        self.assertEqual(service, clone)
        my_cluster: set[cluster.Microservice] = set()
        self.assertEqual(len(my_cluster), 0)
        my_cluster.add(service)
        self.assertEqual(len(my_cluster), 1)
        my_cluster.add(clone)
        self.assertEqual(len(my_cluster), 1)


class MicroserviceManagerTestCase(IsolatedAsyncioTestCase):
    """Microservice manager test."""

    def setUp(self) -> None:

        class MyConfig(MicroserviceConfig):
            pass
        cfg = MyConfig(__file__)
        self.mng = MicroServiceManager(cfg, __file__)

    async def test_check_connection_to_rabbit(self):
        await self.mng.check_connection_to_rabbit_mq()

    async def test_preflight_checks(self):
        await self.mng.preflight_checks()

    def test_get_celery_app(self):
        app = self.mng.get_celery_app()
        self.assertIsInstance(app, Celery)

    def test_base_directories(self) -> None:
        manager = default_app_manager

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
