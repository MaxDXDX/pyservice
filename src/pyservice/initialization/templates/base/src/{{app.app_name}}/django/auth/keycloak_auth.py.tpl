from pyservice.django.keycloak_auth.authentication import KeycloakAuthentication
from {{ app.app_name }} import manager
from {{ app.app_name }}.domain import account as account_domain


log = manager.get_logger_for_pyfile(__file__)


class KeycloakAuth(KeycloakAuthentication):
    log = log
    account_domain_module = account_domain
    app_manager = manager
