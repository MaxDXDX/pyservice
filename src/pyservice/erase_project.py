"""Entrypoint to init new app/microservice."""


from pathlib import Path
import sys

from pyservice.files.files import erase_directory


if __name__ == '__main__':
    current_path = Path(sys.path[0])
    erase_directory(current_path)
    print(f'{current_path} has been erased.')
