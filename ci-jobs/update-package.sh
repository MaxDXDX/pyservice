project_id=$CI_PROJECT_ID

# GITLAB_API_TOKEN lives in the <CI variables> of the gitlab project
api_token=$GITLAB_API_TOKEN

echo "installing tools"
apt update && apt install jq curl -y
python -m pip install -r ./ci-jobs/requirements.txt

echo "updating package in project with id=$project_id"

echo 'removing existed package...'
existed_id=$(curl --header "PRIVATE-TOKEN: $api_token" "${CI_API_V4_URL}/projects/${project_id}/packages" | jq .[].id)
echo "ID of existed package: $existed_id"
curl --request DELETE --header "PRIVATE-TOKEN: $api_token" "${CI_API_V4_URL}/projects/${project_id}/packages/${existed_id}"
echo "existed package with ID=${existed_id} removed"

mkdir -p dist

echo 'building new dist files...'
python -m build
echo 'built files:'
ls dist

echo 'pushing built package to gitlab...'
TWINE_PASSWORD=${CI_JOB_TOKEN} TWINE_USERNAME=gitlab-ci-token python -m twine upload --repository-url "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/pypi" dist/*
