from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from {{ app.app_name }} import config, manager

user_model = get_user_model()

log = manager.get_logger_for_pyfile(__file__)


class Command(BaseCommand):
    help = 'Updating superusers'

    def handle(self, *args, **options):
        log.debug('updating superusers:')
        actual_superusers = config.super_users
        log.debug('- actual superusers: %s', actual_superusers)
        for user in actual_superusers:
            username, password, e_mail = user
            log.debug('updating user: %s', username)
            try:
                existing_user = user_model.objects.all().get(username=username)
            except ObjectDoesNotExist:
                log.debug('user "%s" does not exist, '
                          'creating the new one ...', username)
                new_superuser = user_model.objects.create_superuser(
                    username,
                    e_mail,
                    password,
                    # id=latest_id + 1,
                )
                log.debug('new superuser has been created: %s', new_superuser)
            else:
                log.debug('superuser already exists (%s), updating data ...',
                          existing_user)
                existing_user.set_password(password)
                existing_user.email = e_mail
                existing_user.save()
                log.debug('already present superuser has been updated: %s',
                          existing_user)
        actual_usernames = [_[0] for _ in actual_superusers]
        orphans = user_model.objects.exclude(is_superuser=False).exclude(username__in=actual_usernames)
        if orphans:
            log.debug('orphans: %s', orphans)
            for orphan in orphans:
                log.debug('deleting orphan superuser %s ...', orphan)
                assert orphan.is_superuser
                orphan.delete()
        else:
            log.debug('no orphans detected')

