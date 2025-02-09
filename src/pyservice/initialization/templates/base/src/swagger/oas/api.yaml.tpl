openapi: 3.1.1

security:
  - Keycloak: []

info:
  title: Phoenix Application
  description: |-
    Awesome web application.

  contact:
    email: developer@cebb.pro
  version: 1.0.0

servers:
  - url: /{{ app.url_prefix }}/api/v1/
    description: PRODUCTION
  - url: http://localhost:{{ app.docker_django_port }}/{{ app.url_prefix }}/api/v1/
    description: LOCAL

# tags:
#   - name: Assistants
#     description: Sources of system

paths:
  /account/:
    get:
      tags:
        - Assistants
      summary: Get account data

components:
  schemas:

#  securitySchemes:
#    Keycloak:
#      type: oauth2
#      name: Phoenix
#      description: Сервер авторизации **Феникс**
#      flows:
#        implicit:
#          authorizationUrl: https://auth.cebb.pro/auth/realms/phoenix-production-1/protocol/openid-connect/auth

  securitySchemes:
    Keycloak:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.cebb.pro/auth/realms/phoenix-production-1/protocol/openid-connect/auth
          tokenUrl: https://auth.cebb.pro/auth/realms/phoenix-production-1/protocol/openid-connect/token
          refreshUrl: https://auth.cebb.pro/auth/realms/phoenix-production-1//protocol/openid-connect/token
      x-usePkceWithAuthorizationCodeGrant: true  # Enables PKCE in Swagger UI
#          scopes:
#            read: Read access to protected resources
#            write: Write access to protected resources