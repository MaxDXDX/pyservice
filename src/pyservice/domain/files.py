"""Models for files."""


from __future__ import annotations

import typing as t
from pathlib import Path
from uuid import uuid4
import shutil
import re

from pyservice.mixins.mixins import SequenceMixin
from pyservice.files import files as files_tools

from . import base



class LocalFile(base.BaseEntity):
    """File on local drive."""

    fullpath: Path

    @property
    def _id(self):
        return self.fullpath

    @property
    def md5(self) -> str:
        return files_tools.md5(self.fullpath)

    @property
    def last_extension(self) -> str:
        extension = self.fullpath.suffix.replace('.', '')
        return extension

    @property
    def filename_without_last_extension(self) -> str:
        return self.fullpath.name.replace(f'.{self.last_extension}', '')

    @property
    def name_and_extension(self) -> tuple[str, str]:
        return self.filename_without_last_extension, self.last_extension

    def binary_content(self):
        with open(self.fullpath, 'rb') as f:
            file_content = f.read()
            return file_content

    def rename(
            self,
            new_name: str,
            exist_ok: bool = False,
    ):
        self.move_to_directory(
            directory=self.fullpath.parent,
            new_filename=new_name,
            exist_ok=exist_ok,
        )

    def move_to_directory(
            self,
            directory: Path,
            new_filename: str = None,
            exist_ok: bool = False,
    ):
        if not new_filename:
            new_filename = self.fullpath.name
        new_fullpath = directory / new_filename
        if new_fullpath.is_file():
            if exist_ok:
                new_fullpath.unlink(missing_ok=True)
            else:
                raise FileExistsError(f'File <{new_fullpath}> already exists')
        shutil.move(str(self.fullpath), str(new_fullpath))
        self.fullpath = new_fullpath

    @property
    def is_exist(self) -> bool:
        return self.fullpath.is_file()

    class Examples:
        """Generators for building examples. Usefully for tests."""

        @classmethod
        def random_txt(
                cls,
                directory: Path,
        ) -> LocalFile:
            content = f'this is a random text content: {uuid4()}'
            created_file = files_tools.create_text_file_in_directory(
                directory=directory,
                content=content,
                filename=f'random-txt-file-{uuid4()}.txt'
            )
            return LocalFile(fullpath=created_file)

        @classmethod
        def txt(cls, fullpath: Path, content) -> LocalFile:
            created_file = files_tools.create_text_file_in_directory(
                directory=fullpath.parent,
                content=content,
                filename=fullpath.name,
            )
            return LocalFile(fullpath=created_file)


class LocalFiles(base.BaseEntity, SequenceMixin):
    """Set of files on local drive."""

    items: set[LocalFile]

    @classmethod
    def build_from_native_paths(cls, files: list[Path]) -> LocalFiles:
        items = {LocalFile(fullpath=_) for _ in files}
        return cls(items=items)


    @classmethod
    def build_empty(cls) -> LocalFiles:
        return cls(items=set())


    def move_all_files_to_directory(
            self,
            new_directory: Path,
            exist_ok: bool = False,
    ):
        for _ in self.items:
            _.move_to_directory(
                directory=new_directory,
                exist_ok=exist_ok,
            )

    @property
    def filenames(self) -> list[str]:
        return [_.fullpath.name for _ in self.items]

    def get_by_regex(
        self,
        pattern: t.Union[str, re.Pattern]
    ) -> t.Union[None, LocalFile, list[LocalFile]]:
        """
        Returns files whose filenames match the given regex pattern.

        Args:
            pattern (str | re.Pattern): The regex to match filenames against.

        Returns:
            None: if no files matched
            LocalFile: if exactly one file matched
            list[LocalFile]: if more than one file matched
        """
        regex = re.compile(pattern) if isinstance(pattern, str) else pattern

        matched = [f for f in self.items if regex.search(f.fullpath.name)]

        if not matched:
            return None
        if len(matched) == 1:
            return matched[0]
        return matched
