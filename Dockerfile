# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG BASE_IMAGE
# hadolint ignore=DL3006
FROM ${BASE_IMAGE}
RUN apk add --no-cache bash curl jq  python3

# Suggested by hadolint DL4006:
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install gcloud cli:
RUN curl -sSL https://sdk.cloud.google.com | bash
RUN echo 'source /root/google-cloud-sdk/path.bash.inc' | tee /root/.bashrc > /dev/null