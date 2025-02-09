from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from {{ app.app_name }} import manager
from {{ app.app_name }}.domain import account as account_domain
from {{ app.app_name }}.django.main import models as django_models


from . import base


logger = manager.get_logger_for_pyfile(__file__, with_path=True)


class AccountView(base.RestViewBase):

    def _get(self, request: Request, *args, **kwargs):
        account: account_domain.Account = request.account
        return Response(data=account.serialized(), status=status.HTTP_200_OK)

