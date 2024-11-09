"""Models and logic for initialization."""


from typing import Any

from pathlib import Path

import toml
from pyservice.domain import base
from pyservice.initialization import contents


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


class InitializationData(base.BaseModel):
    """Initialization core."""

    app_name: str
    is_microservice: bool
    description: str = 'Python application.'
    author: str = 'Ross Geller'

    app_dir: Path = None

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

    def create_directories_for_app(self):
        self.src_dir_path.mkdir(exist_ok=True)
        self.root_module_dir_path.mkdir(exist_ok=True)
        self.domain_dir_path.create_as_python_package()
        self.service_dir_path.create_as_python_package()
        if self.is_microservice:
            self.celery_dir_path.mkdir(exist_ok=True)

    def create_files_and_directories(self):
        self.create_directories_for_app()

        self.create_empty_setup_file()
        self.create_pyproject_toml_file()
        self.create_config_file()
        self.create_root_module_init_file()
        self.create_gitignore_file()
        if self.is_microservice:
            self.create_celery_tasks_file()
        self.exceptions_file_path.create_empty()

    def create_empty_setup_file(self):
        content = 'import setuptools\n\nsetuptools.setup()\n'
        self.setup_file_path.create_with_content(content)

    def create_pyproject_toml_file(self):
        content = toml.dumps(self.project_data)
        self.pyproject_toml_file_path.create_with_content(content)

    def create_config_file(self):
        if self.is_microservice:
            self._create_microservice_config_file()
        else:
            raise NotImplementedError

    def _create_microservice_config_file(self):
        content = contents.microservice_config
        self.config_file_path.create_with_content(content)

    def create_root_module_init_file(self):
        if self.is_microservice:
            self._create_microservice_root_module_init_file()
        else:
            raise NotImplementedError

    def _create_microservice_root_module_init_file(self):
        content = contents.microservice_init
        self.root_module_init_file_path.create_with_content(content)

    def create_gitignore_file(self):
        content = contents.gitignore
        self.gitignore_file_path.create_with_content(content)

    def create_celery_tasks_file(self):
        template = contents.celery_tasks
        content = template.replace('{{ app_name }}', self.app_name)
        self.celery_tasks_file.create_with_content(content)
        init_file = FilePath(path=self.celery_dir_path / '__init__.py')
        init_file.create_empty()

    @property
    def src_dir_path(self) -> Path:
        assert self.app_dir
        src_dir = self.app_dir / 'src'
        return src_dir

    @property
    def root_module_dir_path(self) -> Path:
        assert self.app_name
        root_module_dir = self.src_dir_path / self.app_name
        return root_module_dir

    @property
    def domain_dir_path(self) -> DirPath:
        return DirPath(path=self.root_module_dir_path / 'domain')

    @property
    def service_dir_path(self) -> DirPath:
        return DirPath(path=self.root_module_dir_path / 'service')

    @property
    def celery_dir_path(self) -> Path:
        return self.root_module_dir_path / 'celery_tasks'

    @property
    def celery_tasks_file(self) -> FilePath:
        return FilePath(path=self.celery_dir_path / 'tasks.py')

    @property
    def setup_file_path(self) -> FilePath:
        return FilePath(path=self.app_dir / 'setup.py')

    @property
    def pyproject_toml_file_path(self) -> FilePath:
        return FilePath(path=self.app_dir / 'pyproject.toml')

    @property
    def config_file_path(self) -> FilePath:
        return FilePath(path=self.root_module_dir_path / 'config.py')

    @property
    def root_module_init_file_path(self) -> FilePath:
        return FilePath(path=self.root_module_dir_path / '__init__.py')

    @property
    def gitignore_file_path(self) -> FilePath:
        return FilePath(path=self.app_dir / '.gitignore')

    @property
    def exceptions_file_path(self) -> FilePath:
        return FilePath(path=self.root_module_dir_path / 'exceptions.py')

    @property
    def project_data(self) -> dict:
        template = {
            'build-system': {
                'build-backend': 'setuptools.build_meta',
                'requires': [
                    'setuptools'
                ]
            },
            'project': {
                'dependencies': [
                    'pyservice @ git+https://pack:H4maFc_jxo6rnbaNmu8c@'
                    'git.cebb.pro/ias-phoenix-native/submodules/'
                    'pyservice.git@_package',
                ],
                'description': self.description,
                'name': self.app_name,
                'readme': 'README.md',
                'requires-python': '>=3.11',
                'version': '0.0.1',
                'authors': [
                    {
                        'name': self.author,
                    }
                ]
            }
        }
        return template
