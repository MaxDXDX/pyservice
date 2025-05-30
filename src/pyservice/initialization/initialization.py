"""Logic for initialization new app/microservice."""


from pathlib import Path
import subprocess
import sys

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape

from pyservice.initialization.domain import InitializationData
from pyservice.initialization import domain as d
from pyservice.text_tools import text_tools


def gather_init_data_for_app() -> InitializationData:
    app_name = click.prompt(
        'name of application (a-Z,0-9,_): ',
        type=str, default='app')
    is_microservice = click.prompt(
        'is this app plan to be a microservice [True(y), False(n)]: ',
        type=bool, default=True)
    assert isinstance(is_microservice, bool)
    is_django_powered = click.prompt(
        'include Django [True(y), False(n)]: ',
        type=bool, default=True)
    assert isinstance(is_django_powered, bool)

    if is_django_powered:
        docker_db_version = click.prompt(
            'version of postgres db: ',
            type=str, default='17.0')
        docker_nginx_version = click.prompt(
            'version of nginx: ',
            type=str, default='1.24.0')
        docker_django_port = click.prompt(
            'external port for local app`s container: ',
            type=str, default='12001')
        docker_db_port = click.prompt(
            'external port for local db`s container: ',
            type=str, default=str(int(docker_django_port) + 1))
        docker_nginx_port = click.prompt(
            'external port for local nginx`s container: ',
            type=str, default=str(int(docker_django_port) + 2))
        docker_swagger_port = click.prompt(
            'external port for local swagger`s container: ',
            type=str, default=str(int(docker_django_port) + 3))
        docker_rabbit_port = click.prompt(
            'external port for local rabbit`s container: ',
            type=str, default=str(int(docker_django_port) + 4))
        docker_seq_port = click.prompt(
            'external port for local seq`s container: ',
            type=str, default=str(int(docker_django_port) + 5))
        url_prefix = click.prompt(
            'url prefix for all app`s url paths: ',
            type=str, default=text_tools.to_kebab(app_name))

        init_data = InitializationData(
            app_name=app_name,
            is_microservice=is_microservice,
            is_django_powered=is_django_powered,
            docker_django_port=docker_django_port,
            docker_db_port=docker_db_port,
            docker_nginx_port=docker_nginx_port,
            docker_swagger_port=docker_swagger_port,
            docker_rabbit_port=docker_rabbit_port,
            docker_seq_port=docker_seq_port,
            docker_nginx_version=docker_nginx_version,
            docker_db_version=docker_db_version,
            url_prefix=url_prefix,
        )
        return init_data
    else:
        raise NotImplementedError


def build_scaffold(app_init_data: InitializationData):
    args_for_templates = {
        'app': app_init_data,
    }

    dir_with_templates = Path(__file__).parent / 'templates' / 'base'
    tpl_env = Environment(
        loader=FileSystemLoader(dir_with_templates),
        autoescape=select_autoescape()
    )
    destination_dir = app_init_data.app_dir
    all_templates = []

    for i in tpl_env.list_templates():
        if '.tpl' in str(i):
            jinja_template = tpl_env.get_template(i)
            t = d.FileTemplate(
                jinja=jinja_template,
                path=Path(i),
                destination_directory=destination_dir,
                args=args_for_templates,
            )
            all_templates.append(t)

    for template in all_templates:
        template.render()


def init_new_service(app_dir: Path):
    print(f'initializing new service at {app_dir}:')
    init_data = gather_init_data_for_app()
    init_data.app_dir = app_dir
    print(init_data.as_yaml())
    build_scaffold(init_data)

    print('project structure has been created, installing dependencies ...')
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', '-e', '.'])
    except subprocess.CalledProcessError as e:
        print('Error during install app as package:')
        print(e.returncode)
        print(e.stderr)
        print(e.output)
        print(e.stdout)
        print('try to run manually:\npython -m pip install -e .')

    print('all dependencies have been installed\n')
    print(
        f'now manually run db and seq docker containers:\n'
        f'- docker compose up db seq -d\n'
        f'Then make initial migrations:\n'
        f'- python src/{init_data.app_name}/django/manage.py makemigrations\n'
        f'Then build all images:\n'
        f'- docker compose build\n'
        f'And run all containers:\n'
        f'- docker compose up\n'
    )



