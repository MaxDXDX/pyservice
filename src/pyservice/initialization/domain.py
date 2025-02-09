"""Models and logic for initialization."""
from typing import Any
from pathlib import Path

import jinja2 as j

from pyservice.domain import base
from pyservice.files import files


class FilePath(base.BaseModel):
    """Path to file."""

    path: Path

    # pylint: disable=C0103
    def model_post_init(self, __context: Any) -> None:
        assert not self.path.is_dir()

    def create_with_content(self, content: str):
        self.path.unlink(missing_ok=True)
        with open(self.path, 'w', encoding='UTF-8') as f:
            f.write(content)

    def create_empty(self):
        self.create_with_content(content='')


class DirPath(base.BaseModel):
    """Path to directory."""

    path: Path

    # pylint: disable=C0103
    def model_post_init(self, __context: Any) -> None:
        assert not self.path.is_file()

    def create(self, exist_ok: bool = True):
        self.path.mkdir(exist_ok=exist_ok)

    def create_as_python_package(self):
        self.create()
        empty_init_file = FilePath(path=self.path / '__init__.py')
        empty_init_file.create_empty()


class FileTemplate(base.BaseModelWithArbitraryFields):
    """Template for project`s file."""
    jinja: j.Template
    path: Path
    destination_directory: Path
    args: dict

    @property
    def destination_filename(self) -> str:
        return self.path.name.replace('.tpl', '')

    @property
    def destination_file_directory(self) -> Path:
        as_str = str(self.destination_directory / self.path.parent)
        as_tpl = j.Environment(loader=j.BaseLoader()).from_string(as_str)
        after_rendering = Path(as_tpl.render(self.args))
        after_rendering.mkdir(parents=True, exist_ok=True)
        return after_rendering

    @property
    def destination_fullpath(self) -> Path:
        return self.destination_file_directory / self.destination_filename

    @property
    def destination_directory_for_file(self) -> Path:
        return self.destination_directory / self.path.parent

    def render(self):
        content = self.jinja.render(self.args)
        files.save_text(content, self.destination_fullpath)


class InitializationData(base.BaseModel):
    """Initialization core."""

    app_name: str
    is_microservice: bool
    is_django_powered: bool
    description: str = 'Python application.'
    author: str = 'Ross Geller'

    app_dir: Path = None

    docker_django_port: str
    docker_db_version: str = '17.0'
    docker_nginx_version: str = '1.22.0'

    docker_db_port: str
    docker_nginx_port: str
    docker_swagger_port: str
    docker_rabbit_port: str
    docker_seq_port: str

    url_prefix: str = 'prefix'

    # pylint: disable=C0103
    def model_post_init(self, __context: Any) -> None:
        restricted_app_names = [
            'pyservice',
            'examples',
        ]
        if self.app_name in restricted_app_names:
            raise ValueError(
                f'You can not use the name "{self.app_name}" for your app. '
                f'It is reserved for system purposes.')
