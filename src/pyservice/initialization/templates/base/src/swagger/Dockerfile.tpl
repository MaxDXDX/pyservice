FROM swaggerapi/swagger-ui
ENV SWAGGER_JSON=/tmp/oas/api.yaml
ENV OAUTH_CLIENT_ID=meta-aggregator-light-client
ENV OAUTH_APP_NAME='REST API'
COPY ./oas /tmp/oas

