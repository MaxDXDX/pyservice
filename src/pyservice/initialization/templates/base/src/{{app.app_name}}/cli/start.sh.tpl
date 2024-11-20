set -e

app_ref=$(python service.py manager app_ref)

echo "========================================================================"
echo "${app_ref} SERVICE"
echo "========================================================================"
printenv && pip list
echo "========================================================================"
echo "service config:"
python service.py config as_yaml
python service.py manager print_summary

########## CELERY #####################################:

python preflight_checks.py

tmp_dir=$(python service.py manager directory_for_tmp)
log_dir=$(python service.py manager directory_for_logs)
python service.py manager erase_tmp_directory
# shellcheck disable=SC2115
echo "Tmp directory content (must be empty):"
ls "${tmp_dir}" -al
all_queues=$(python service.py manager all_queues --as_text=True)
echo "All queues of service: ${all_queues}"
echo "starting celery with queues: ${all_queues}"
command_for_restart_celery="celery multi restart w1 -A ${app_ref}:celery_app -l DEBUG --purge -B -Q ${all_queues} --pidfile=${tmp_dir}/%n.pid --logfile=${log_dir}/%n%I.log"
echo "${command_for_restart_celery}" > restart-celery.sh
celery multi restart w1 -A "${app_ref}:celery_app" -l DEBUG --purge -B -Q "${all_queues}" --pidfile="${tmp_dir}/%n.pid" --logfile="${log_dir}/%n%I.log"
#celery -A "${app_ref}:celery_app" worker -l INFO --purge -B -Q "${all_queues}"
echo 'celery started, testing it...'
python service.py manager check_celery_test_files
echo 'celery is working!!!'
########################################################

python service.py manager on_start
# shellcheck disable=SC2155
source run-django.sh

tail -f /dev/null
