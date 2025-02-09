"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from {{ app.app_name }} import manager

from . import views as v
from .rest import urls as rest_patterns


base_patterns = [
    path('admin/config/', v.ConfigView.as_view()),
    path('admin/', admin.site.urls),

    path('api/v1/', include(rest_patterns.rest_api_patterns))
]

if manager.config.url_prefix:
    urlpatterns = [
        path(f'{manager.config.url_prefix}/', include(base_patterns)),
    ]
else:
    urlpatterns = base_patterns
