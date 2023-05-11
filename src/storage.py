# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.cloud import storage


def upload_to_gcs(bucket: str, name: str, data: str):
    """Upload a string to Google Cloud Storage bucket.

    Args:
      bucket (str): the name of the Storage bucket. Do not include "gs://"
      name (str): the name of the file to create in the bucket
      data (str): the data to store

    """
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(name)
    blob.upload_from_string(data)
