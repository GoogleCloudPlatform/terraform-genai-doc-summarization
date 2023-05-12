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
import datetime
import re

from document_extract import async_document_extract
from storage import upload_to_gcs
from vertex_llm import predict_large_language_model_hack


def coerce_datetime_zulu(input_datetime: datetime.datetime):
    """Force datetime into specific format.

    Args:
      input_datetime (datetime.datetime): the datetime to coerce

    """
    regex = re.compile(r"(.*)(Z$)")
    regex_match = regex.search(input_datetime)
    if regex_match:
        assert input_datetime.startswith(regex_match.group(1))
        assert input_datetime.endswith(regex_match.group(2))
        return datetime.datetime.fromisoformat(f'{input_datetime[:-1]}+00:00')
    raise RuntimeError(
        'The input datetime is not in the expected format. '
        'Please check format of the input datetime. Expected "Z" at the end'
    )


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
@functions_framework.cloud_event
def entrypoint(cloud_event) -> dict:
    """Entrypoint for Cloud Function

    Args:
      cloud_event (CloudEvent): an event from EventArc

    Returns:
      dictionary with 'summary' and 'output_filename' keys
    """

    event_id = cloud_event["id"]
    event_type = cloud_event["type"]
    bucket = cloud_event.data["bucket"]
    name = cloud_event.data["name"]
    metageneration = cloud_event.data["metageneration"]
    timeCreated = coerce_datetime_zulu(cloud_event.data["timeCreated"])
    updated = coerce_datetime_zulu(cloud_event.data["updated"])

    extracted_text = async_document_extract(bucket, name)
    summary = predict_large_language_model_hack(
        project_id="velociraptor-16p1-src",
        model_name="text-bison-001",
        temperature=0.2,
        max_decode_steps=1024,
        top_p=0.8,
        top_k=40,
        content=f'Summarize:\n{extracted_text}',
        location="us-central1",
    )

    output_filename = f'{name.replace(".pdf", "")}_summary.txt'
    upload_to_gcs(
        bucket,
        output_filename,
        summary,
    )

    return {
        'summary': summary,
        'output_filename': output_filename,
    }
