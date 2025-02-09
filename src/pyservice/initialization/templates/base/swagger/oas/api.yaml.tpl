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
#   - name: Some tag
#     description: Description of tag

paths:
  /account/:
    get:
      tags:
        - Assistants
      summary: Get account data (as example)
      responses:
        '200':
          description: Account info
          content:
            application/json:
              example:
                id: "65a2ef19-bc5a-4433-9e50-ec332b861ea5"
                username: "ivan"
                last_name: "Ivanov"
                first_name: "Ivan"

components:
  schemas:

  securitySchemes:
    Keycloak:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.cebb.pro/auth/realms/phoenix-production-1/protocol/openid-connect/auth
          tokenUrl: https://auth.cebb.pro/auth/realms/phoenix-production-1/protocol/openid-connect/token
          refreshUrl: https://auth.cebb.pro/auth/realms/phoenix-production-1//protocol/openid-connect/token
      x-usePkceWithAuthorizationCodeGrant: true  # Enables PKCE in Swagger UI