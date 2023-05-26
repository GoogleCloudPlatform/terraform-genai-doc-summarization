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

import datetime
import json
import os
import re

import cloudevents.http
import functions_framework
import flask.wrappers
from google.auth import default
from google.cloud import logging
import vertexai
from vertexai.preview.language_models import TextGenerationModel

# from bigquery import write_summarization_to_table
# from document_extract import async_document_extract
# from storage import upload_to_gcs
# from vertex_llm import predict_large_language_model
# from utils import coerce_datetime_zulu, truncate_complete_text

_PROJECT_ID = os.environ['PROJECT_ID']
_LOCATION = os.environ['LOCATION']
_CREDENTIALS, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
_DEFAULT_PARAMETERS = {
    "temperature": .2,
    "max_output_tokens": 256,
    "top_p": .95,
    "top_k": 40,
}


def coerce_datetime_zulu(input_datetime: str) -> datetime.datetime:

    regex = re.compile(r"(.*)(Z$)")
    regex_match = regex.search(input_datetime)
    if regex_match:
        assert input_datetime.startswith(regex_match.group(1))
        assert input_datetime.endswith(regex_match.group(2))
        return datetime.datetime.fromisoformat(f'{input_datetime[:-1]}+00:00')
    raise RuntimeError(
        'The input datetime is not in the expected format. '
        'Please check the format of the input datetime. Expected "Z" at the end'
    )


def default_marshaller(o: object) -> str:
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return str(o)


def summarize_text(text: str, parameters: None | dict[str, int | float] = None) -> str:
    """Summarization Example with a Large Language Model"""
    vertexai.init(
        project=_PROJECT_ID,
        location=_LOCATION,
        credentials=_CREDENTIALS
    )

    final_parameters = _DEFAULT_PARAMETERS.copy()
    if parameters:
        final_parameters.update(parameters)

    model = TextGenerationModel.from_pretrained("text-bison@001")
    response = model.predict(
        f'Provide a summary with about two sentences for the following article: {text}\n'
        'Summary:',
        **final_parameters,
    )
    print(f"Response from Model: {response.text}")

    return response.text


def entrypoint(request: object) -> dict[str, str]:
    
    if isinstance(request, cloudevents.http.CloudEvent):
        return cloud_event_entrypoint(request)
    elif isinstance(request, flask.wrappers.Request):
        return flask_entrypoint(request)
    else:
        raise Exception  # TODO raise a descriptive exception


def flask_entrypoint(request):
    return 'FLASK_ENTRYPOINT'


@functions_framework.cloud_event
def cloud_event_entrypoint(cloud_event: cloudevents.http.CloudEvent):

    metadata = dict(
        event_id=cloud_event["id"],
        event_type=cloud_event["type"],
        bucket=cloud_event.data["bucket"],
        name=cloud_event.data["name"],
        metageneration=cloud_event.data["metageneration"],
        timeCreated=coerce_datetime_zulu(cloud_event.data["timeCreated"]),
        updated=coerce_datetime_zulu(cloud_event.data["updated"]),
    )

    try:
        response = {
            'revision': os.environ['REVISION'],
            'summary': summarize_text(_MOCK_TEXT),
        }
    except Exception as e:
        response = {
            'exception': str(e),
        }
    response['metadata'] = metadata

    print(json.dumps({'response': response}, indent=2, sort_keys=True, default=default_marshaller))

    return response
