user  nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log notice;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main
      '$time_iso8601 | '
      'ra:$remote_addr '
      '[$scheme://$host:$server_port -> $proxy_host] '
      'up:$upstream_addr '
      'ru:$remote_user '
      '"$request" '
      '$status '
      '[times(r|ur|uc|uh): $request_time | $upstream_response_time | $upstream_connect_time | $upstream_header_time ] '
      '$body_bytes_sent '
      '"$http_referer" '
      '"$http_user_agent" '
      'xff:"$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;

    #gzip  on;

#    server {
#      listen 80;
#    }

    client_max_body_size 20M;

    types {
        text/plain log;
    }

    server {
        listen       80;

        location /{{ app.url_prefix }}/static {
            alias /artefacts/static;
        }

        location /{{ app.url_prefix }}/logs {
            charset utf-8;
            autoindex on;
            alias /artefacts/logs;
        }

        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   /usr/share/nginx/html;
        }
    }
}
