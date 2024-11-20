FROM nginx:{{ app.docker_nginx_version }}

RUN rm -rf /etc/nginx/conf.d/ && rm /etc/nginx/nginx.conf
COPY ./nginx.conf /etc/nginx/
