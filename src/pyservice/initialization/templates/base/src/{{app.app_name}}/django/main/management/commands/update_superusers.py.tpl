from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from {{ app.app_name }} import manager


user_model = get_user_model()
log = manager.get_logger_for_pyfile(__file__)


class Command(BaseCommand):
    help = 'Updating superusers from config'

    def handle(self, *args, **options):
        print('updating superusers from config ...', end='')
        updated_superusers = user_model.update_superusers()
        print(f' done ({len(updated_superusers)} users)')

