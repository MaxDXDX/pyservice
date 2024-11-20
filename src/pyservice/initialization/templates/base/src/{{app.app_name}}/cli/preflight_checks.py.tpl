import asyncio
from {{ app.app_name }} import manager


if __name__ == '__main__':
    asyncio.run(manager.preflight_checks())
