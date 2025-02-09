from django.contrib import admin

from {{ app.app_name }}.django.main import models


class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'global_uuid',
        'username',
        'last_name',
        'first_name',
        'roles',
    )

admin.site.register(models.Account, AccountAdmin)