from __future__ import annotations

from {{ app.app_name }} import manager

from .model_base import BaseDjangoModel

log = manager.get_logger_for_pyfile(__file__)


# class MyModel(BaseDjangoModel):
#     some_field = models.TextField(null=True, blank=True)
