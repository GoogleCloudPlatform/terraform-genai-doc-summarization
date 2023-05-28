#!/bin/bash
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -e

if [ -z "$(git status --porcelain)" ]; then 
  REVISION="$(git rev-parse --short HEAD)"
else 
  echo "Git repo is dirty, continuing anyway..."
  REVISION="DIRTY_REPO"
  # echo "Git repo is dirty, cancelling deployment..."
  # exit 1
fi

source config.env

DESTROY=
while (( ${#} > 0 )); do
  case "${1}" in
    ( '--destroy' | '-d' ) DESTROY='-destroy' ;;      # Handles --destroy
    ( '--' ) operands+=( "${@:2}" ); break ;;         # End of options
    ( '-'?* ) ;;                                      # Discard non-valid options
    ( * ) operands+=( "${1}" )                        # Handles operands
  esac
  shift
done

gcloud config set project "${PROJECT_ID?}"
gcloud --quiet auth login "${PRINCIPAL?}" --no-launch-browser
gcloud services enable cloudresourcemanager.googleapis.com

docker build --build-arg BASE_IMAGE="${BASE_TERRAFORM_IMAGE?}" -t "${TERRAFORM_IMAGE?}" .

docker run \
  -w /app \
  -v "$(pwd)"/terraform:/app \
  "${TERRAFORM_IMAGE?}" \
  init \
  -upgrade \
  -reconfigure \
  -backend-config="access_token=$(gcloud auth print-access-token)" \
  -backend-config="bucket=${TF_PLAN_STORAGE_BUCKET?}" \
  -backend-config="prefix=${PREFIX?}"

docker run \
  -w /app \
  -v "$(pwd)"/terraform:/app \
  -e GOOGLE_OAUTH_ACCESS_TOKEN="$(gcloud auth print-access-token)" \
  "${TERRAFORM_IMAGE?}" \
  apply \
  --auto-approve \
  -var project_id="${PROJECT_ID?}" \
  -var region="${REGION?}" \
  -var bucket="${BUCKET?}" \
  -var principal="${PRINCIPAL?}" \
  -var revision="${REVISION?}" \
  -var access_token="${ACCESS_TOKEN?}" \
  "${DESTROY?}"
