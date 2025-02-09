"""Base classes for building REST API views."""


from logging import Logger
from datetime import datetime as dt

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
