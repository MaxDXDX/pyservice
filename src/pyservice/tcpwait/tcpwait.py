"""Function for waiting TCP ports."""

import asyncio
import dataclasses
from datetime import datetime as dt
from typing import Type


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


TcpServiceFormat = Type[TcpService | tuple[str, str | int] | str]


def normalize_tcp_service(
        initial: TcpServiceFormat) -> TcpService:
    if isinstance(initial, tuple):
        return TcpService(*initial)
    elif isinstance(initial, TcpService):
        return initial
    elif isinstance(initial, str):
        if ':' not in initial:
            raise ValueError(f'incorrect format for tcp service - {initial}')
        parts = initial.partition(':')
        hostname = parts[0]
        port = int(parts[2])
        return TcpService(hostname, port)
    else:
        raise ValueError(f'incorrect format for tcp service - {initial}')


async def wait_for_tcp_service(
        target: TcpServiceFormat,
        timeout: int = 10,
        check_period: int = 1,
) -> TcpService:
    target = normalize_tcp_service(target)
    start_at = dt.now()
    print(f'start waiting for TCP service {target} for {timeout} seconds:')
    while True:
        try:
            print(f'try to connect to TCP service {target}...', end='')
            await asyncio.open_connection(target.hostname, target.port)
        except (ConnectionRefusedError, asyncio.TimeoutError, OSError) as e:
            print(f' NOT READY YET, waiting {check_period} second(s)...')
            duration = (dt.now() - start_at).total_seconds()
            if duration > timeout:
                raise TcpServiceUnavailable(str(target)) from e
            await asyncio.sleep(check_period)
        else:
            target.is_ready = True
            print(' READY!')
            return target


