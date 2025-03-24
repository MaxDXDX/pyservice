default:
  tags:
    - new-runner

stages:
  - build
  - apply

build-nginx:
  stage: build
  image: docker:24.0.5
  services:
    - docker:24.0.5-dind
  variables:
    SERVICE: nginx
    DOCKER_FILE: ./nginx/Dockerfile
    DOCKER_CONTEXT: ./nginx
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - export IMAGE=$CI_REGISTRY_IMAGE/$SERVICE/$DEPLOY_ENVIRONMENT_TYPE:$IMAGE_TAG
    - echo "Name for image - ${IMAGE}"
    - docker build -t $IMAGE -f $DOCKER_FILE $DOCKER_CONTEXT
    - docker push $IMAGE
    - echo "Image ${IMAGE} has been pushed to Container Registry"
  rules:
    - if: $CI_COMMIT_TAG
    - if: $CI_COMMIT_BRANCH == "master"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"
    - if: $CI_COMMIT_BRANCH == "dev"


build-swagger:
  stage: build
  image: docker:24.0.5
  services:
    - docker:24.0.5-dind
  variables:
    SERVICE: swagger
    DOCKER_FILE: ./swagger/Dockerfile
    DOCKER_CONTEXT: ./swagger
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - export IMAGE=$CI_REGISTRY_IMAGE/$SERVICE/$DEPLOY_ENVIRONMENT_TYPE:$IMAGE_TAG
    - echo "Name for image - ${IMAGE}"
    - docker build -t $IMAGE -f $DOCKER_FILE $DOCKER_CONTEXT
    - docker push $IMAGE
    - echo "Image ${IMAGE} has been pushed to Container Registry"
  rules:
    - if: $CI_COMMIT_TAG
    - if: $CI_COMMIT_BRANCH == "master"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"
    - if: $CI_COMMIT_BRANCH == "dev"


build-django:
  stage: build
  image: docker:24.0.5
  services:
    - docker:24.0.5-dind
  variables:
    SERVICE: django
    DOCKER_FILE: ./Dockerfile
    DOCKER_CONTEXT: .
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - export IMAGE=$CI_REGISTRY_IMAGE/$SERVICE/$DEPLOY_ENVIRONMENT_TYPE:$IMAGE_TAG
    - echo "Name for image - ${IMAGE}"
    - docker build -t $IMAGE -f $DOCKER_FILE $DOCKER_CONTEXT
    - docker push $IMAGE
    - echo "Image ${IMAGE} has been pushed to Container Registry"
  rules:
    - if: $CI_COMMIT_TAG
    - if: $CI_COMMIT_BRANCH == "master"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"
    - if: $CI_COMMIT_BRANCH == "dev"

apply-in-production-cluster:
  stage: apply
  image:
    name: fluxcd/flux-cli:v2.0.1
    entrypoint: ['']
  variables:
    LABEL: $CI_PROJECT_PATH_SLUG
    SELECTOR: gitlab.project=$CI_PROJECT_PATH_SLUG
  script:
    - kubectl config use-context $GITLAB_AGENT
    - kubectl get deployments -l $SELECTOR
    - kubectl delete deployments -l $SELECTOR
  rules:
    - if: $CI_COMMIT_BRANCH == "master"
    - if: $CI_COMMIT_BRANCH == "main"


apply-in-develop-cluster:
  stage: apply
  image:
    name: fluxcd/flux-cli:v2.0.1
    entrypoint: ['']
  variables:
    LABEL: $CI_PROJECT_PATH_SLUG
    SELECTOR: gitlab.project=$CI_PROJECT_PATH_SLUG
  script:
    - kubectl config use-context $GITLAB_AGENT
    - kubectl get deployments -l $SELECTOR
    - kubectl delete deployments -l $SELECTOR
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"
    - if: $CI_COMMIT_BRANCH == "dev"
