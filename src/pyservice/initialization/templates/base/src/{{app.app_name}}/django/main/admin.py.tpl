from django.contrib import admin, messages
from django.utils.translation import ngettext

from {{ app.app_name }}.django.main import models


# admin for your model:
# class MyModel(admin.ModelAdmin):
#     list_display = (
#         'some_field',
#     )


# admin.site.register(models.MyModel, MyModel)
