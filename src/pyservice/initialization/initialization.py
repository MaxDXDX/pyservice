"""Logic for initialization new app/microservice."""


from pathlib import Path

import click

from pyservice.initialization.domain import InitializationData


def gather_init_data_for_app() -> InitializationData:
    app_name = click.prompt(
        'name of application (a-Z,0-9,_): ',
        type=str, default='app')
    is_microservice = click.prompt(
        'is this app plan to be a microservice [True(y), False(n)]: ',
        type=bool, default=True)
    assert isinstance(is_microservice, bool)

    init_data = InitializationData(
        app_name=app_name,
        is_microservice=is_microservice,
    )
    return init_data


def init_new_service(app_dir: Path):
    print(f'initializing new service at {app_dir}:')
    init_data = gather_init_data_for_app()
    init_data.app_dir = app_dir
    print(init_data.as_yaml())
    init_data.create_files_and_directories()






