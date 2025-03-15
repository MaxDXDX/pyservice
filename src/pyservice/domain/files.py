"""Models for files."""


from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import shutil

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
