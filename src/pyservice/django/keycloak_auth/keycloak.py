# pylint: skip-file

""" module for app specific keycloak connection """
from typing import Dict, List
import logging

from keycloak import KeycloakOpenID

from .settings import api_settings
from . import ref


log = logging.getLogger(ref)


def get_keycloak_openid(oidc: dict = None) -> KeycloakOpenID:
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
            server_url=api_settings.KEYCLOAK_SERVER_URL,
            realm_name=api_settings.KEYCLOAK_REALM,
            client_id=api_settings.KEYCLOAK_CLIENT_ID,
            client_secret_key=api_settings.KEYCLOAK_CLIENT_SECRET_KEY
        )
    except KeyError as e:
        raise KeyError(
            f'invalid settings: {e}'
        ) from e


def get_resource_roles(decoded_token: Dict, client_id=None) -> List[str]:
    """
    Get roles from access token
    """
    resource_access_roles = []
    try:
        if client_id is None:
            client_id = api_settings.KEYCLOAK_CLIENT_ID

        log.debug(f'{__name__} - get_resource_roles - client_id: {client_id}')
        resource_access_roles = (
            decoded_token['resource_access']
            [client_id]
            ['roles']
        )
        roles = add_role_prefix(resource_access_roles)
        log.debug(f'{__name__} - get_resource_roles - roles: {roles}')

        return roles
    except Exception as e:
        log.warning(f'{__name__} - get_resource_roles - Exception: {e}')
        return []


def add_role_prefix(roles: List[str]) -> List[str]:
    """
    add role prefix configured by KEYCLOAK_ROLE_SET_PREFIX to a list of roles
    """
    log.debug(f'{__name__} - get_resource_roles - roles: {roles}')
    prefixed_roles = [prefix_role(x) for x in roles]
    log.debug(
        f'{__name__} - get_resource_roles - prefixed_roles: {prefixed_roles}'
    )
    return prefixed_roles


def prefix_role(role: str) -> str:
    """ add prefix to role string """
    role_prefix = (
        api_settings.KEYCLOAK_ROLE_SET_PREFIX
        if api_settings.KEYCLOAK_ROLE_SET_PREFIX
        and isinstance(api_settings.KEYCLOAK_ROLE_SET_PREFIX, str)
        else ''
    )
    return f'{role_prefix}{role}'
