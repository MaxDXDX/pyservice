"""Base classes for building REST API views."""
import uuid
from logging import Logger
from datetime import datetime as dt
import pathlib

from django.http import FileResponse
from django.core.files import uploadedfile
from django.core.files import storage
from rest_framework.request import Request
from rest_framework.views import APIView

from pyservice.time_periods.duration import Duration
from pyservice.manager.manager import DjangoBasedMicroserviceManager


class RestViewBaseAbstract(APIView):
    """Base view. Use it for real views."""

    started_at: dt = None
    log: Logger
    app_manager: DjangoBasedMicroserviceManager

    @property
    def current_duration(self) -> Duration:
        assert self.started_at
        return Duration(
            start=self.started_at,
            end=self.app_manager.get_now(),
        )

    def get(self, request: Request, *args, **kwargs):
        """GET handler."""
        self._pre_processing_actions(request, *args, **kwargs)
        result = self._get(request, *args, **kwargs)
        self._log_end(request, *args, **kwargs)
        return result

    def _get(self, request, *args, **kwargs):
        raise NotImplementedError

    def delete(self, request: Request, *args, **kwargs):
        """DELETE handler."""
        self._pre_processing_actions(request, *args, **kwargs)
        result = self._delete(request, *args, **kwargs)
        self._log_end(request, *args, **kwargs)
        return result

    def _delete(self, request, *args, **kwargs):
        raise NotImplementedError

    def put(self, request: Request, *args, **kwargs):
        """PUT handler."""
        self._pre_processing_actions(request, *args, **kwargs)
        result = self._put(request, *args, **kwargs)
        self._log_end(request, *args, **kwargs)
        return result

    def _put(self, request, *args, **kwargs):
        raise NotImplementedError

    def post(self, request: Request, *args, **kwargs):
        """POST handler."""
        self._pre_processing_actions(request, *args, **kwargs)
        result = self._post(request, *args, **kwargs)
        self._log_end(request, *args, **kwargs)
        return result

    def _post(self, request, *args, **kwargs):
        raise NotImplementedError

    def _pre_processing_actions(self, request, *args, **kwargs):
        self._log_start(request, *args, **kwargs)

    def _log_start(self, request, *args, **kwargs):
        method = request.method
        self.log.debug(
            'request has been registered: '
            '%s | '  # method
            'view: %s | '
            'args: %s | '
            'kwargs: %s |',
           method,type(self).__name__, args, kwargs
        )
        self.started_at = self.app_manager.get_now()

    # pylint: disable=W0613
    def _log_end(self, request, *args, **kwargs):
        duration = self.current_duration
        self.log.debug('response time: %s', duration.pretty_seconds)


    def dispatch(self, request: Request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        return result

    def make_subdir_for_tmp_files(self) -> pathlib.Path:
        now_point_without_dot = str(dt.now().timestamp()).replace('.', '')
        random_uuid = uuid.uuid4()
        target_dir = self.app_manager.directory_for_tmp / f'{now_point_without_dot}_{random_uuid}'
        target_dir.mkdir(exist_ok=False)
        return target_dir


    def save_incoming_files_to_tmp_dir(
            self,
            # pylint:disable=line-too-long
            files_from_request: list[uploadedfile.InMemoryUploadedFile | uploadedfile.TemporaryUploadedFile]
    ) -> list[pathlib.Path]:
        now_point_without_dot = str(dt.now().timestamp()).replace('.', '')
        random_uuid = uuid.uuid4()
        target_dir = self.make_subdir_for_tmp_files()
        stack = []
        for _ in files_from_request:
            if not isinstance(_, str):
                saved = self.save_incoming_file_to_tmp_dir(
                    _, target_dir=target_dir)
                stack.append(saved)
        return stack

    def save_incoming_file_to_tmp_dir(
            self,
            # pylint:disable=line-too-long
            file_from_request: uploadedfile.InMemoryUploadedFile | uploadedfile.TemporaryUploadedFile,
            target_dir: pathlib.Path = None,
    ) -> pathlib.Path:
        if not target_dir:
            target_dir = self.make_subdir_for_tmp_files()
        target_fullpath = target_dir / file_from_request.name
        self.log.debug(
            'saving uploaded file %s as: %s',
            file_from_request, target_fullpath)

        is_file_with_same_filename_exists = target_fullpath.is_file()
        if is_file_with_same_filename_exists:
            self.log.critical('ERROR during saving file from request - '
                         'file with same name is already exists: %s',
                         target_fullpath
                         )
            raise RuntimeError(
                f'File {target_fullpath} is already exists!')
        storage.FileSystemStorage(location=target_fullpath.parent).save(
            target_fullpath.name, file_from_request)
        if not target_fullpath.is_file():
            raise RuntimeError('ERROR during saving file from request '
                               'to temporary file')
        self.log.debug('File has been saved to: %s', target_fullpath)
        return target_fullpath

    @staticmethod
    def build_file_response(
            full_path: pathlib.Path,
    ) -> FileResponse:
        # pylint:disable=consider-using-with
        response = FileResponse(
            open(full_path, 'rb'),
            content_type='application/pdf',
            filename=full_path.name,  # optional for Content-Disposition
            as_attachment=False  # IMPORTANT: inline display
        )
        # response['Cache-Control'] = 'max-age=60'
        return response
