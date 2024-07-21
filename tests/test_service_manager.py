"""
Tests.
"""

from unittest import IsolatedAsyncioTestCase
from celery import Celery

from pyservice.pyconfig.pyconfig import MicroserviceConfig
from pyservice.manager.manager import MicroServiceManager


class MicroserviceManagerTestCase(IsolatedAsyncioTestCase):
    """Microservice manager test."""

    def setUp(self) -> None:

        class MyConfig(MicroserviceConfig):
            service_ref = 'my_micro_service'
        cfg = MyConfig(config_file=__file__)
        self.mng = MicroServiceManager(cfg)

    async def test_check_connection_to_rabbit(self):
        await self.mng.check_connection_to_rabbit_mq()

    async def test_preflight_checks(self):
        await self.mng.preflight_checks()

    def test_get_celery_app(self):
        app = self.mng.get_celery_app()
        self.assertIsInstance(app, Celery)

