"""
Tests.
"""

from unittest import IsolatedAsyncioTestCase

from pyservice.tcpwait import tcpwait


class TcpWait(IsolatedAsyncioTestCase):
    """Test case."""

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

    async def test_wait_for_service_bad_path(self):
        target = ('localhost', 7567)
        with self.assertRaises(tcpwait.TcpServiceUnavailable):
            found = await tcpwait.wait_for_tcp_service(target, 1)
            self.assertIsInstance(found, tcpwait.TcpService)
            self.assertFalse(found.is_ready)
