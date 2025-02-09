from django.urls import path

from . import account as account_views

rest_api_patterns = [
    path('account/', account_views.AccountView.as_view()),
]
