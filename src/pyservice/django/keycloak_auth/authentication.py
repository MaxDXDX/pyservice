# pylint: skip-file

""" Keycloak authentication class specific to Django Rest Framework """

import uuid
from typing import Tuple, Dict, List
from datetime import datetime as dt

from django.contrib.auth.models import AnonymousUser, update_last_login, Group
from django.contrib.auth import get_user_model

from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
# from rest_framework.settings import APISettings

# from keycloak import KeycloakOpenID

from pyservice.manager.manager import DjangoBasedMicroserviceManager
from pyservice.time_periods.duration import Duration

from .keycloak import KeycloakLogic

# from .keycloak import (
#     get_keycloak_openid,
#     get_resource_roles,
#     add_role_prefix
# )
# from .settings import api_settings
from . import ref


User = get_user_model()
# api_settings = APISettings()


class OIDCConfigException(Exception):
    pass


class KeycloakAuthentication(authentication.TokenAuthentication):
    keyword = 'Bearer'

    account_domain_module = None
    app_manager: DjangoBasedMicroserviceManager = None
    log = None
    keycloak_logic = KeycloakLogic

    keycloak_openid = None

    def __init__(self):
        self.keycloak_logic = KeycloakLogic(app_manager=self.app_manager)

    def authenticate(self, request):
        self.log.debug('Start Keycloak Authentication for request %s', request)
        start = dt.now()
        if self.keycloak_openid is None:
            self.keycloak_openid = self.keycloak_logic.get_keycloak_openid()

        credentials = super().authenticate(request)
        if credentials:
            user, decoded_token = credentials
            # if api_settings.KEYCLOAK_MANAGE_LOCAL_GROUPS is True:
            #     groups = self._get_or_create_groups(request.roles)
            #     user.groups.set(groups)
            self._user_toggle_is_staff(request, user)
            self.log.debug('authenticated django account: %s', user)
            account_domain = user.to_domain()
            self.log.debug(
                'domain account for authenticated django account: '
                '%s, roles: %s',
                account_domain, account_domain.roles)
            request.account = account_domain

            # filtered_roles = [_.replace('role:', '')
            #                   for _ in roles if 'role' in _]
            # user.roles = filtered_roles
            # self.log.debug('user: %s (%s)', user, type(user))
            # # self.log.debug('roles: %s', user.roles)
            # request.account = account_domain
        self.log.debug('KC auth finished, total duration: %s',
                  Duration(start=start, end=dt.now()).as_pretty_string)
        return credentials


    def authenticate_credentials(
        self,
        key: str
    ) -> Tuple[AnonymousUser, Dict]:
        """ Attempt to verify JWT from Authorization header with Keycloak """
        self.log.debug('KeycloakAuthentication.authenticate_credentials')
        try:
            user = None
            # Checks token is active
            decoded_token = self._get_decoded_token(key)
            self.log.debug('decoded token: %s', decoded_token)
            self._verify_token_active(decoded_token)
            # if api_settings.KEYCLOAK_MANAGE_LOCAL_USER is not True:
            #     self.log.debug(
            #         'KeycloakAuthentication.authenticate_credentials: '
            #         f'{decoded_token}'
            #     )
            #     user = AnonymousUser()
            # else:
            user = self._handle_local_user(decoded_token)

            self.log.debug(
                'KeycloakAuthentication.authenticate_credentials: '
                f'{user} | {decoded_token}'
            )
            return (user, decoded_token)
        except Exception as e:
            self.log.error(
                'KeycloakAuthentication.authenticate_credentials | '
                f'Exception: {e}'
            )
            self.log.exception(e)
            raise AuthenticationFailed() from e

    def _get_decoded_token(self, token: str) -> dict:
        return self.keycloak_openid.introspect(token)

    def _verify_token_active(self, decoded_token: dict) -> None:
        """ raises if not active """
        is_active = decoded_token.get('active', False)
        if not is_active:
            raise AuthenticationFailed(
                'invalid or expired token'
            )

    def get_role_refs_from_decoded_token(
            self, decoded_token: dict
    ) -> dict:
        refs = {
            'client': [],
            'realm': [],
            'all': [],
        }
        client_roles = (decoded_token
                        .get('resource_access', {})
                        .get(self.app_manager.config.keycloak_client_id, {})
                        .get('roles', []))
        realm_roles = (decoded_token
                       .get('realm_access', {})
                       .get('roles', [])
                       )
        refs['client'] = client_roles if client_roles else []
        refs['realm'] = realm_roles if realm_roles else []
        refs['all'] = refs['client'] + refs['realm']
        self.log.debug('refs of roles from token: %s', refs)
        return refs

    def get_roles_from_token(
            self, decoded_token: dict):
        refs = self.get_role_refs_from_decoded_token(decoded_token)
        all_roles = self.account_domain_module.Roles.build_from_list_of_refs(refs['all'])
        return all_roles

    def _build_domain_account_from_decoded_token(self, decoded_token: dict):
        self.log.debug(
            'building domain account from decoded token: %s', decoded_token)
        global_uuid = uuid.UUID(decoded_token.get('global_uuid'))
        email = decoded_token.get('email', '')
        first_name = decoded_token.get('given_name', '')
        last_name = decoded_token.get('family_name', '')
        username = decoded_token['username']
        all_roles = self.get_roles_from_token(decoded_token)
        self.log.debug(
            '- global_uuid: %s\n'
            '- username: %s\n'
            '- last_name: %s\n'
            '- first_name: %s\n'
            '- email: %s\n'
            '- all_known_roles: %s\n'
            '',
            global_uuid,
            username,
            last_name,
            first_name,
            email,
            all_roles,
        )
        domain_account = self.account_domain_module.Account(
            id=global_uuid,
            username=username,
            last_name=last_name,
            first_name=first_name,
            roles=all_roles,
        )
        return domain_account

    def _update_user(self, user: User, django_fields: dict) -> User:
        """ if user exists, keep data updated as necessary """
        save_model = False

        for key, value in django_fields.items():
            try:
                if getattr(user, key) != value:
                    setattr(user, key, value)
                    save_model = True
            except Exception:
                self.log.warning(
                    'KeycloakAuthentication.'
                    '_update_user | '
                    f'setattr: {key} field does not exist'
                )
        self.log.debug('updated user info before updating it in django: %s', user)
        if save_model:
            user.save()
        return user

    @staticmethod
    def extract_session_id(decoded_token):
        session_id = decoded_token.get('sid')
        return session_id

    def _handle_local_user(self, decoded_token: dict) -> User:
        """ used to update/create local users from keycloak data """
        domain_account = self._build_domain_account_from_decoded_token(
            decoded_token
        )
        self.log.debug('updating built account in django account model ...')
        User.update_from_domain(domain_account)
        try:
            django_account = User.update_from_domain(domain_account)
        except Exception as e:
            self.log.critical(
                'Error during updating domain account %s', domain_account)
            self.log.exception(e)
            raise e
        update_last_login(sender=None, user=django_account)
        return django_account

    def _get_roles(
        self,
        user: User,
        decoded_token: dict
    ) -> List[str]:
        """ try to add roles from authenticated keycloak user """
        roles = []
        try:
            roles += self.keycloak_logic.get_resource_roles(
                decoded_token,
                self.keycloak_openid.client_id
            )
            roles.append(str(user.pk))
        except Exception as e:
            self.log.warning(
                'KeycloakAuthentication._get_roles | '
                f'Exception: {e}'
            )

        self.log.debug(f'KeycloakAuthentication._get_roles: {roles}')
        return roles

    def _get_or_create_groups(self, roles: List[str]) -> List[Group]:
        groups = []
        for role in roles:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.log.debug(
                    'KeycloakAuthentication._get_or_create_groups | created: '
                    f'{group.name}'
                )
            else:
                self.log.debug(
                    'KeycloakAuthentication._get_or_create_groups | exists: '
                    f'{group.name}'
                )
            groups.append(group)
        return groups

    def _user_toggle_is_staff(self, request, user: User) -> None:
        """
        toggle user.is_staff if a role mapping has been declared in settings
        """
        try:
            # catch None or django.contrib.auth.models.AnonymousUser
            valid_user = bool(
                user
                and isinstance(user, User)
                and hasattr(user, 'is_staff')
                and getattr(user, 'is_superuser', False) is False
            )
            self.log.debug(
                f'KeycloakAuthentication._user_toggle_is_staff | {user} | '
                f'valid_user: {valid_user}'
            )
            # if (
            #     valid_user
            #     and api_settings.KEYCLOAK_ROLES_TO_DJANGO_IS_STAFF
            #     and type(api_settings.KEYCLOAK_ROLES_TO_DJANGO_IS_STAFF)
            #     in [list, tuple, set]
            # ):
            #     is_staff_roles = set(
            #         self.keycloak_logic.add_role_prefix(
            #             api_settings.KEYCLOAK_ROLES_TO_DJANGO_IS_STAFF
            #         )
            #     )
            #     self.log.debug(
            #         f'KeycloakAuthentication._user_toggle_is_staff | {user} | '
            #         f'is_staff_roles: {is_staff_roles}'
            #     )
            #     user_roles = set(request.roles)
            #     self.log.debug(
            #         f'KeycloakAuthentication._user_toggle_is_staff | {user} | '
            #         f'user_roles: {user_roles}'
            #     )
            #     is_staff = bool(is_staff_roles.intersection(user_roles))
            #     self.log.debug(
            #         f'KeycloakAuthentication._user_toggle_is_staff | {user} | '
            #         f'is_staff: {is_staff}'
            #     )
            #     # don't write unnecessarily, check different first
            #     if is_staff != user.is_staff:
            #         user.is_staff = is_staff
            #         user.save()
        except Exception as e:
            self.log.warning(
                'KeycloakAuthentication._user_toggle_is_staff | '
                f'Exception: {e}'
            )


# class KeycloakMultiAuthentication(KeycloakAuthentication):
#
#     def authenticate(self, request):
#         if api_settings.KEYCLOAK_MULTI_OIDC_JSON is None:
#             self.log.warning(
#                 'KeycloakMultiAuthentication.authenticate | '
#                 'api_settings.KEYCLOAK_MULTI_OIDC_JSON is empty'
#             )
#             return None
#
#         credentials = None
#
#         def get_host_oidc(hostname: str, oidc_dict: dict) -> KeycloakOpenID:
#             for key, oidc in oidc_dict.items():
#                 if key in str(hostname):
#                     self.log.info(f"get_host_oidc: Found OIDC adapter for '{hostname}'")
#                     return self.keycloak_logic.get_keycloak_openid(oidc)
#             return None
#
#         # Resolve OIDC adapter by hostname
#         if isinstance(api_settings.KEYCLOAK_MULTI_OIDC_JSON, dict):
#             try:
#                 self.keycloak_openid = get_host_oidc(
#                     request.get_host(),
#                     api_settings.KEYCLOAK_MULTI_OIDC_JSON)
#
#                 if self.keycloak_openid is None:
#                     raise OIDCConfigException(f"Could not determine OIDC adapter for "
#                                         f"'{str(request.get_host())}'. Trying all")
#
#                 credentials = super().authenticate(request)
#                 if credentials:
#                     # Append realm_name
#                     credentials[1].update(
#                         {'realm_name': self.keycloak_openid.realm_name}
#                     )
#                     return credentials
#
#             except OIDCConfigException as e:
#                 self.log.warning(
#                     'KeycloakMultiAuthentication.authenticate | '
#                     f'OIDCConfigException: {e})'
#                 )
#
#             except AuthenticationFailed as e:
#                 self.log.info(
#                     'KeycloakMultiAuthentication.authenticate | '
#                     f'AuthenticationFailed: {e})'
#                 )
#
#             except Exception as e:
#                 self.log.error(
#                     'KeycloakMultiAuthentication.authenticate | '
#                     f'Exception: {e})'
#                 )
#
#         # Legacy
#         else:
#             self.log.info("(Deprecated) Using legacy OIDC authentication")
#             for oidc in api_settings.KEYCLOAK_MULTI_OIDC_JSON:
#                 try:
#                     self.keycloak_openid = self.keycloak_logic.get_keycloak_openid(oidc)
#
#                     credentials = super().authenticate(request)
#                     if credentials:
#                         # Append realm_name
#                         credentials[1].update(
#                             {'realm_name': self.keycloak_openid.realm_name}
#                         )
#                         break
#
#                 except AuthenticationFailed as e:
#                     self.log.info(
#                         'KeycloakMultiAuthentication.authenticate | '
#                         f'AuthenticationFailed: {e})'
#                     )
#
#                 except Exception as e:
#                     self.log.error(
#                         'KeycloakMultiAuthentication.authenticate | '
#                         f'Exception: {e} ({self.keycloak_openid.realm_name})'
#                     )
#
#         return credentials
