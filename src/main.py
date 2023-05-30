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

import functions_framework

from dataclasses import dataclass

from google.cloud import logging

from .bigquery import write_summarization_to_table
from .document_extract import async_document_extract
from .storage import upload_to_gcs
from .vertex_llm import predict_large_language_model
from .utils import coerce_datetime_zulu, truncate_complete_text

FUNCTIONS_GCS_EVENT_LOGGER = 'function-triggered-by-storage'
# TODO(erschmid): replace PROJECT_ID, MODEL_NAME, TABLE_ID, and DATASET_ID
# with env vars
PROJECT_ID = 'velociraptor-16p2-dev'
OUTPUT_BUCKET = 'velociraptor-16p2-src'
MODEL_NAME = 'text-bison@001'
DATASET_ID = 'academic_papers'
TABLE_ID = 'summarizations'


@dataclass
class CloudEventData:
    event_id:  str
    event_type:  str
    bucket:  str
    name:  str
    metageneration:  str
    timeCreated:  str
    updated:  str

    @classmethod
    def read_datetimes(cls, kwargs):
        for key in ['timeCreated', 'updated']:
            kwargs[key] = coerce_datetime_zulu(kwargs.pop(key))

        return cls(**kwargs)


# WEBHOOK FUNCTION
# @functions_framework.cloud_request
def entrypoint(request):
    """Entrypoint for Cloud Function"""

    print(request.get_json())
    return "HelloWorld!!!!"
