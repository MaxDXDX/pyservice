"""
Common functions for deals with directories and files.
"""


import shutil
import json
import pathlib
from pathlib import Path
import aiofiles
import tarfile


def normalized_path(path: str | Path) -> Path:
    if isinstance(path, str):
        path = Path(path)
    return path


def normalize_path(func_for_path):
    def wrapper(path: Path | str, *args, **kwargs):
        if isinstance(path, str):
            path = Path(path)
        return func_for_path(path, *args, **kwargs)
    return wrapper


def compress_file_or_directory_by_tar(
        file_or_directory: Path,
        output_dir_or_file: Path = None) -> Path:
    origin_parent = file_or_directory.parent
    origin_name = file_or_directory.name

    if not output_dir_or_file:
        output_filename = f'{origin_name}.tar.gz'
        output = origin_parent / output_filename
    elif output_dir_or_file.is_file():
        raise FileExistsError(f'File is already exists - {output_dir_or_file}')
    elif output_dir_or_file.is_dir():
        output_filename = f'{origin_name}.tar.gz'
        output = output_dir_or_file / output_filename
    else:
        raise ValueError(f'Can not compress {file_or_directory}')

    with tarfile.open(output, 'w:gz') as tar:
        tar.add(
            file_or_directory,
            arcname=file_or_directory.name
        )

    assert output.is_file()
    return output


def extract_data_from_tar_archive(
        tar_archive: Path,
        output_dir: Path = None,
        ignore_single_root_dir: bool = True):
    if not output_dir:
        output_dir = tar_archive.parent

    # print('TAR E')
    # print(tar_archive)
    # print(output_dir)
    with tarfile.open(tar_archive) as t:
        def strip(member, path: Path):  # pylint: disable=W0613:
            return member.replace(name=Path(*Path(member.path).parts[1:]))
        fn = strip if ignore_single_root_dir else None
        t.extractall(path=output_dir, filter=fn)
        t.close()


def create_text_file_in_directory(
        directory: Path, content: str = None, filename: str = None
) -> Path:
    if not content:
        content = 'this is a test content'
    if not filename:
        filename = 'test-text-file'

    full_path = directory / filename
    full_path.unlink(missing_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return full_path


@normalize_path
def erase_directory(directory: Path):
    assert not directory.is_file()
    assert directory.is_dir()
    all_entities = directory.glob('**/*')
    files = [x for x in all_entities if x.is_file()]
    for _ in files:
        _.unlink()
    dirs = directory.glob('**/*')
    for _ in dirs:
        shutil.rmtree(_)


@normalize_path
def get_list_of_files_and_directories_in_directory(
        directory: Path, mask: str = '**/*') -> tuple[list[Path], list[Path]]:
    all_entities = directory.glob(mask)
    files = []
    directories = []
    for _ in all_entities:
        if _.is_file():
            files.append(_)
        elif _.is_dir():
            directories.append(_)
        else:
            raise ValueError(f'Can not detect the type of <{_}>: '
                             f'it is not file or directory')
    return files, directories


@normalize_path
def get_list_of_directories_in_directory(
        directory: Path, mask: str = '**/*'
) -> list[Path]:
    # pylint: disable=W0612
    files, directories = get_list_of_files_and_directories_in_directory(
        directory, mask)
    return directories


@normalize_path
def get_list_of_files_in_directory(
        directory: Path, mask: str = '**/*'
) -> list[Path]:
    # pylint: disable=W0612
    files, directories = get_list_of_files_and_directories_in_directory(
        directory, mask)
    return files


@normalize_path
def get_number_of_files_and_directories_in_directory(
        directory: Path) -> tuple[int, int]:
    files, directories = get_list_of_files_and_directories_in_directory(
        directory)
    return len(files), len(directories)


@normalize_path
def get_number_of_files_in_directory(directory: Path) -> int:
    return len(get_list_of_files_in_directory(directory))


@normalize_path
def get_number_of_directories_in_directory(directory: Path) -> int:
    return len(get_list_of_directories_in_directory(directory))


def find_first_file(mask: str, path: str | pathlib.Path):
    found = sorted(path.glob(mask))
    if found:
        return found[0]


def find_files_for_set_of_years(
        years: list,
        tag_in_filename: str,
        folder: pathlib.Path,
):
    found_files = []
    for year in years:
        found = find_first_file(
            mask=f'{tag_in_filename}-{year}' + '*',
            path=folder
        )
        if found:
            found_files.append((year, found))
    if len(years) == len(found_files):
        return found_files


async def get_content_of_found_file_in_folder(
        file_mask: str,
        folder_path: str | pathlib.Path
) -> str | dict | list | None:
    folder_path = normalized_path(folder_path)
    file = find_first_file(
        mask=file_mask,
        path=folder_path
    )
    if file:
        async with aiofiles.open(file, mode='r', encoding='utf-8') as f:
            response = await f.read()
            try:
                data = json.loads(response)
            except json.decoder.JSONDecodeError:
                return response
            else:
                return data


def get_content_of_found_file_in_folder__sync(
        file_mask: str,
        folder_path: str | pathlib.Path
) -> str | dict | list | None:
    folder_path = normalized_path(folder_path)
    file = find_first_file(
        mask=file_mask,
        path=folder_path
    )
    if file:
        with open(file, mode='r', encoding='utf-8') as f:
            response = f.read()
            try:
                data = json.loads(response)
            except json.decoder.JSONDecodeError:
                return response
            else:
                return data


def save_dict_or_list(content: dict, full_path, indented=True):
    if isinstance(content, (dict, list)):
        with open(full_path, 'w', encoding='utf-8') as f:
            indent = 2 if indented else None
            json.dump(content, f, ensure_ascii=False, indent=indent)
