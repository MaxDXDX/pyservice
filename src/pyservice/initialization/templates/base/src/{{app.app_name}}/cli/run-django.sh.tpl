#!/bin/bash

initial_directory=$(pwd)

django_directory=$(python service.py manager django_directory)
web_static_files_directory=$(python service.py manager web_static_files_directory)
is_django_server_in_dev_mode=$(python service.py config is_django_server_in_dev_mode)
gunicorn_config_file_path=$(python service.py manager gunicorn_config_file_path)

echo "django directory - ${django_directory}"
echo "directory for web static files - ${web_static_files_directory}"
echo "is django should be started in develop mode - ${is_django_server_in_dev_mode}"
echo "gunicorn config file - ${gunicorn_config_file_path}"
# shellcheck disable=SC2164
cd "${django_directory}"


# common django actions:
python manage.py migrate
python manage.py migrate main
python manage.py update_superusers

echo "Collecting all static files in one folder to serve it by NGINX ..."
python manage.py collectstatic --noinput
echo "static files have been collected: "
ls "${web_static_files_directory}"

echo
if [ "${is_django_server_in_dev_mode}" == "True" ]
  then
    echo "Starting built-in develop django server"
    python manage.py runserver 0.0.0.0:8000
  else
    echo "Starting production gunicorn server"
    rm -rf /gunicorn.pid
    gunicorn -c "${gunicorn_config_file_path}"
    tail -f /dev/null
fi

# shellcheck disable=SC2164
cd "${initial_directory}"
