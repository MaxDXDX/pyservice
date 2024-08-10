"""
Common functions for deals with directories and files.
"""
import shutil
import json
import pathlib
from pathlib import Path
import aiofiles
import tarfile


def format_bytes(size, should_round: bool = True):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0: '', 1: 'k', 2: 'm', 3: 'g', 4: 't'}
    while size > power:
        size /= power
        n += 1
    if should_round:
        size = round(size, 1)
    return str(size) + power_labels[n] + 'b'


def create_if_not_yet(func):
    def wrapper(*args):
        path: Path = func(*args)
        path.mkdir(exist_ok=True, parents=True)
        return path
    return wrapper


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
        file_or_directory: Path | str,
        output_dir_or_file: Path | str = None) -> Path:
    file_or_directory = Path(file_or_directory)
    if output_dir_or_file:
        output_dir_or_file = Path(output_dir_or_file)
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
        output = output_dir_or_file

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


class SetOfFileSystemEntities:
    """The set of files, dirs and other file-system entities."""

    files: set[Path]
    directories: set[Path]
    symlinks: set[Path]
    sockets: set[Path]
    char_devices: set[Path]
    fifos: set[Path]
    block_devices: set[Path]
    mounts: set[Path]
    denied: set[Path]
    unknown: set[Path]

    entity_types = [
        'files',
        'directories',
        'symlinks',
        'sockets',
        'char_devices',
        'fifos',
        'block_devices',
        'mounts',
        'denied',
        'unknown',
    ]

    def __init__(self):
        self.clear()

    @property
    def total_entities(self):
        counts = [len(getattr(self, _)) for _ in self.entity_types]
        return sum(counts)

    def clear(self):
        for _ in self.entity_types:
            setattr(self, _, set())

    @property
    def total_size_in_bytes(self):
        file_sizes = [_.lstat().st_size for _ in self.files if _.is_file()]
        result = sum(file_sizes)
        return result

    @property
    def total_size_for_human(self):
        return format_bytes(self.total_size_in_bytes)

    def __repr__(self):
        rows = [
            f'total size - {self.total_size_for_human}',
        ]
        for entity_type in self.entity_types:
            entities = getattr(self, entity_type)
            count = len(entities)
            if count:
                as_text = f'- {entity_type}: {count}'
                rows.append(as_text)
        return '\n'.join(rows)


class DetailedDirectory:
    """Full statistic for directory."""

    directory: Path
    entities: SetOfFileSystemEntities
    mask: str

    def __init__(self, directory: Path | str, mask: str = '**/*'):
        self.mask = mask
        self.entities = SetOfFileSystemEntities()
        self.directory = Path(directory)
        self.parse()

    def parse(self):
        assert self.directory.is_dir()
        self.entities.clear()
        unfiltered_entities = list(self.directory.glob(self.mask))
        for _ in unfiltered_entities:
            try:
                if _.is_file():
                    self.entities.files.add(_)
                elif _.is_dir():
                    self.entities.directories.add(_)
                elif _.is_socket():
                    self.entities.sockets.add(_)
                elif _.is_symlink():
                    self.entities.symlinks.add(_)
                elif _.is_char_device():
                    self.entities.symlinks.add(_)
                elif _.is_fifo():
                    self.entities.fifos.add(_)
                elif _.is_block_device():
                    self.entities.block_devices.add(_)
                elif _.is_mount():
                    self.entities.mounts.add(_)
                else:
                    self.entities.unknown.add(_)
            except PermissionError:
                self.entities.denied.add(_)

    def __repr__(self):
        header = str(self.directory)
        content = repr(self.entities)
        return '\n'.join([header, content])


@normalize_path
def get_list_of_directories_in_directory(
        directory: Path, mask: str = '**/*'
) -> list[Path] | set[Path]:
    detailed_dir = DetailedDirectory(directory, mask=mask)
    return detailed_dir.entities.directories


@normalize_path
def get_list_of_files_in_directory(
        directory: Path, mask: str = '**/*'
) -> list[Path] | set[Path]:
    detailed_dir = DetailedDirectory(directory, mask=mask)
    return detailed_dir.entities.files


@normalize_path
def get_number_of_files_and_directories_in_directory(
        directory: Path) -> tuple[int, int]:
    detailed_dir = DetailedDirectory(directory)
    files = detailed_dir.entities.files
    directories = detailed_dir.entities.directories
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
