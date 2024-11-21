"""Function for waiting TCP ports."""

import logging
import asyncio
import dataclasses
from datetime import datetime as dt
from typing import Type
from pydantic import HttpUrl
from pydantic_core import Url


log = logging.getLogger()


class TcpServiceUnavailable(Exception):
    pass


@dataclasses.dataclass
class TcpService:
    hostname: str
    port: int | str
    is_ready: bool = False

    def __post_init__(self):
        self.port = int(self.port)

    def __repr__(self):
        return f'<TCP {self.hostname}:{self.port}>'


TcpServiceFormat = Type[TcpService | tuple[str, str | int] | str | HttpUrl]


def normalize_tcp_service(
        initial: TcpServiceFormat) -> TcpService:
    type_name = str(type(initial))
    if isinstance(initial, tuple):
        return TcpService(*initial)
    elif isinstance(initial, TcpService):
        return initial
    elif '.Url' in type_name or 'HttpUrl' in type_name:
        hostname = initial.host
        port = initial.port
        return TcpService(hostname, port)
    elif isinstance(initial, str):
        if '://' not in initial:
            if ':' not in initial:
                raise ValueError(
                    f'incorrect format for tcp service - {initial}, '
                    f'type - {type(initial)}')
            else:
                hostname = initial.partition(':')[0]
                port = initial.partition(':')[2]
                try:
                    port = int(port)
                except TypeError as e:
                    raise ValueError(
                        f'incorrect format for tcp service - {initial}, '
                        f'type - {type(initial)}') from e
                else:
                    return TcpService(hostname, port)

        else:
            url = Url(initial)
            return normalize_tcp_service(url)
        # print('url', url)
        # if initial[-1] == '/':
        #     initial = initial[:-1]
        # initial = initial.strip()
        # scheme = initial.partition('://')[0]
        # without_scheme = initial.partition('://')[2]
        # is_http = scheme == 'http'
        # is_https = scheme == 'https'
        # if not is_http and not is_https and ':' not in initial:
        #     raise ValueError(f'incorrect format for tcp service - {initial}')
        # if not is_http and not is_https:
        #     parts = initial.partition(':')
        #     hostname = parts[0]
        #     port = int(parts[2])
        # else:
        #     if ':' in without_scheme:
        #         port = without_scheme.partition(':')[2]
        #         hostname = without_scheme.partition(':')[0]
        #     else:
        #         port = 80 if 'http://' in initial else 443
        #         hostname = initial.partition('://')[2].partition('/')[0]
        # return TcpService(hostname, port)
    else:
        raise ValueError(f'incorrect format for tcp service - {initial}, '
                         f'type - {type(initial)}')


async def wait_for_tcp_service(
        target: TcpServiceFormat,
        timeout: int = 10,
        check_period: int = 1,
) -> TcpService:
    target = normalize_tcp_service(target)
    start_at = dt.now()
    log.debug('start waiting for TCP service %s for %s seconds:',
              target, timeout)
    while True:
        try:
            log.debug('attempt to connect to %s', target.hostname)
            await asyncio.open_connection(target.hostname, target.port)
        except (ConnectionRefusedError, asyncio.TimeoutError, OSError) as e:
            log.debug('it seems that %s is not ready yet, '
                      'sleeping %s sec. before next attempt',
                      target, check_period)
            duration = (dt.now() - start_at).total_seconds()
            if duration > timeout:
                log.exception(e)
                raise TcpServiceUnavailable(str(target)) from e
            await asyncio.sleep(check_period)
        else:
            target.is_ready = True
            log.info('ok - TCP service %s is on wire!', target)
            return target


