# pylint: skip-file

""" module for app specific keycloak connection """
from typing import Dict, List
import logging

from keycloak import KeycloakOpenID

from pyservice.manager.manager import DjangoBasedMicroserviceManager

from . import ref


log = logging.getLogger(ref)


class KeycloakLogic:
    app_manager: DjangoBasedMicroserviceManager

    def __init__(self, app_manager: DjangoBasedMicroserviceManager):
        self.app_manager = app_manager

    @property
    def normalized_keycloak_url(self) -> str:
        original = str(self.app_manager.config.keycloak_url)
        if original[-1] != '/':
            return original + '/'
        return original

    def get_keycloak_openid(self, oidc: dict = None) -> KeycloakOpenID:
        try:
            if oidc:
                log.info(
                    'get_keycloak_openid: '
                    f'OIDC realm={oidc["realm"]}'
                )

                return KeycloakOpenID(
                    server_url=oidc["auth-server-url"],
                    realm_name=oidc["realm"],
                    client_id=oidc["resource"],
                    client_secret_key=oidc["credentials"]["secret"]
                )

            return KeycloakOpenID(
                server_url=self.normalized_keycloak_url,
                realm_name=self.app_manager.config.keycloak_realm,
                client_id=self.app_manager.config.keycloak_client_id,
                client_secret_key=self.app_manager.config.keycloak_secret_key,
            )
        except KeyError as e:
            raise KeyError(
                f'invalid settings: {e}'
            ) from e


    def get_resource_roles(self, decoded_token: Dict, client_id=None) -> List[str]:
        """
        Get roles from access token
        """
        resource_access_roles = []
        try:
            if client_id is None:
                client_id = self.app_manager.config.keycloak_client_id

            log.debug(f'{__name__} - get_resource_roles - client_id: {client_id}')
            resource_access_roles = (
                decoded_token['resource_access']
                [client_id]
                ['roles']
            )
            roles = self.add_role_prefix(resource_access_roles)
            log.debug(f'{__name__} - get_resource_roles - roles: {roles}')

            return roles
        except Exception as e:
            log.warning(f'{__name__} - get_resource_roles - Exception: {e}')
            return []


    def add_role_prefix(self, roles: List[str]) -> List[str]:
        """
        add role prefix configured by KEYCLOAK_ROLE_SET_PREFIX to a list of roles
        """
        log.debug(f'{__name__} - get_resource_roles - roles: {roles}')
        prefixed_roles = [self.prefix_role(x) for x in roles]
        log.debug(
            f'{__name__} - get_resource_roles - prefixed_roles: {prefixed_roles}'
        )
        return prefixed_roles


    def prefix_role(self, role: str) -> str:
        """ add prefix to role string """
        role_prefix = 'role:'
        return f'{role_prefix}{role}'
