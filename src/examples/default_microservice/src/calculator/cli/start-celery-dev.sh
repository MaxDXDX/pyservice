#!/bin/bash

########## CELERY #####################################:
root_module_name=$(python service.py config root_module_name)
tmp_dir=$(python service.py config directory_for_tmp)
log_dir=$(python service.py config directory_for_logs)
echo "- tmp dir: ${tmp_dir}"
echo "- log_dir: ${log_dir}"
echo "The name of root module: ${root_module_name}"
all_queues=$(python service.py manager all_queues --as_text=True)
echo "All queues of service: ${all_queues}"
echo "starting celery with queues: ${all_queues}"
#celery -A "${root_module_name}:celery_app" worker -l INFO --purge -B -Q "${all_queues}"
celery -A "${root_module_name}:celery_app" worker -l DEBUG --purge -B -Q "${all_queues}"
########################################################