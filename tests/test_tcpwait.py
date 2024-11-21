"""
Tests.
"""

from unittest import IsolatedAsyncioTestCase

from pyservice.tcpwait import tcpwait

from pydantic import HttpUrl


class TcpWait(IsolatedAsyncioTestCase):
    """Test case."""

    def test_normalizing(self):
        tests = [
            ('tcp://111.222.333.444:5555', '111.222.333.444', 5555),
            ('http://example.com', 'example.com', 80),
            ('https://example.com', 'example.com', 443),
            ('http://example.com/path/', 'example.com', 80),
            ('https://example.com/path/', 'example.com', 443),
            ('my-hostname:9999', 'my-hostname', 9999),
        ]
        for as_text, hostname, port in tests:
            normalized = tcpwait.normalize_tcp_service(as_text)
            self.assertEqual(hostname, normalized.hostname)
            self.assertEqual(port, normalized.port)

    async def test_wait_for_service_as_tuple(self):
        target_as_tuple = ('google.com', 443)
        found = await tcpwait.wait_for_tcp_service(target_as_tuple, 2)
        self.assertIsInstance(found, tcpwait.TcpService)
        self.assertTrue(found.is_ready)

    async def test_wait_for_service_as_string(self):
        target_as_string = 'google.com:443'
        found = await tcpwait.wait_for_tcp_service(target_as_string, 2)
        self.assertIsInstance(found, tcpwait.TcpService)
        self.assertTrue(found.is_ready)

    async def test_wait_for_service_as_text_http(self):
        google: HttpUrl = 'https://www.google.ru/intl/en/about/products'
        found = await tcpwait.wait_for_tcp_service(google, 2)
        self.assertIsInstance(found, tcpwait.TcpService)
        self.assertTrue(found.is_ready)

    async def test_wait_for_service_as_pydantic_url(self):
        google = HttpUrl(url='https://www.google.ru/intl/en/about/products')
        found = await tcpwait.wait_for_tcp_service(google, 2)
        self.assertIsInstance(found, tcpwait.TcpService)
        self.assertTrue(found.is_ready)

    async def test_wait_for_service_bad_path(self):
        target = ('localhost', 7567)
        with self.assertRaises(tcpwait.TcpServiceUnavailable):
            found = await tcpwait.wait_for_tcp_service(target, 1)
            self.assertIsInstance(found, tcpwait.TcpService)
            self.assertFalse(found.is_ready)
