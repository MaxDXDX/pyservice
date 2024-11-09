"""Entrypoint to init new app/microservice."""


from pathlib import Path
import sys

from pyservice.initialization import initialization


if __name__ == '__main__':
    current_path = Path(sys.path[0])
    initialization.init_new_service(app_dir=current_path)
