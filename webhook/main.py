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
import os
from google.cloud import logging
from typing import Mapping
import google.auth.transport.requests
import google.oauth2.id_token
import requests
import flask

from bigquery import write_summarization_to_table
from document_extract import async_document_extract
from storage import upload_to_gcs
from vertex_llm import predict_large_language_model
from utils import coerce_datetime_zulu, truncate_complete_text

_FUNCTIONS_VERTEX_EVENT_LOGGER = 'summarization-by-llm'

_PROJECT_ID = os.environ["PROJECT_ID"]
_OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
_LOCATION = os.environ["LOCATION"]
_MODEL_NAME = "text-bison@001"
_DEFAULT_PARAMETERS = {
    "temperature": 0.2,
    "max_output_tokens": 256,
    "top_p": 0.95,
    "top_k": 40,
}
_DATASET_ID = os.environ["DATASET_ID"]
_TABLE_ID = os.environ["TABLE_ID"]


def default_marshaller(o: object) -> str:
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return str(o)


def redirect_and_reply(previous_data):
    endpoint = f'https://{_LOCATION}-{_PROJECT_ID}.cloudfunctions.net/{os.environ["K_SERVICE"]}'
    logging_client = logging.Client()
    logger = logging_client.logger(_FUNCTIONS_VERTEX_EVENT_LOGGER)

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, endpoint)
    data = {
        'name': previous_data["name"],
        'id': previous_data["id"],
        'bucket': previous_data["bucket"],
        'timeCreated': previous_data["timeCreated"],
    }
    headers = {}
    headers["Authorization"] = f"Bearer {id_token}"
    logger.log(f'TRIGGERING JOB FLOW: {endpoint}')
    try:
        requests.post(
            endpoint,
            json=data,
            timeout=1,
            headers=headers,
        )
    except requests.exceptions.Timeout:
        return flask.Response(status=200)
    except Exception:
        return flask.Response(status=500)
    return flask.Response(status=200)


def entrypoint(request: object) -> Mapping[str, str]:
    data = request.get_json()
    if data.get("kind", None) == "storage#object":
        # Entrypoint called by Pub-Sub (Eventarc)
        return redirect_and_reply(data)

    if 'bucket' in data:
        # Entrypoint called by REST (possibly by redirect_and_replay)
        return cloud_event_entrypoint(
            name=data["name"],
            event_id=data["id"],
            bucket=data["bucket"],
            time_created=coerce_datetime_zulu(data["timeCreated"]),
        )

    if "text" in data:
        # Entrypoint called by REST.
        return summarization_entrypoint(
            name=data["name"],
            extracted_text=data["text"],
            time_created=datetime.datetime.now(datetime.timezone.utc),
            event_id="CURL_TRIGGER",
        )

    return flask.Response(status=500)


def cloud_event_entrypoint(event_id, bucket, name, time_created):
    orig_pdf_uri = f"gs://{bucket}/{name}"
    logging_client = logging.Client()

    logger = logging_client.logger(_FUNCTIONS_VERTEX_EVENT_LOGGER)
    logger.log(f"cloud_event_id({event_id}): UPLOAD {orig_pdf_uri}",
               severity="INFO")

    extracted_text = async_document_extract(bucket, name, output_bucket=_OUTPUT_BUCKET)
    logger.log(
        f"cloud_event_id({event_id}): OCR  gs://{bucket}/{name}", severity="INFO"
    )

    return summarization_entrypoint(
        name,
        extracted_text,
        time_created=time_created,
        event_id=event_id,
        bucket=bucket,
    )


def summarization_entrypoint(
    name: str,
    extracted_text: str,
    time_created: datetime.time,
    bucket: str = None,
    event_id: str = None,
) -> Mapping[str, str]:
    logging_client = logging.Client()
    logger = logging_client.logger(_FUNCTIONS_VERTEX_EVENT_LOGGER)

    if len(extracted_text) == 0:
        logger.log(f"""cloud_event_id({event_id}): BAD INPUT
No characters recognized from PDF and so the PDF cannot be
summarized. Be sure to upload a high-quality PDF that contains 'Abstract' and
'Conclusion' sections.
                   """, severity="ERROR")
        return ""

    complete_text_filename = f'summaries/{name.replace(".pdf", "")}_fulltext.txt'
    upload_to_gcs(
        _OUTPUT_BUCKET,
        complete_text_filename,
        extracted_text,
    )
    logger.log(
        f"cloud_event_id({event_id}): FULLTEXT_UPLOAD {complete_text_filename}",
        severity="INFO",
    )

    prompt = 'Summarize:'
    extracted_text_trunc = truncate_complete_text(extracted_text, _FUNCTIONS_VERTEX_EVENT_LOGGER)
    summary = predict_large_language_model(
        project_id=_PROJECT_ID,
        model_name=_MODEL_NAME,
        temperature=0.2,
        max_decode_steps=1024,
        top_p=0.8,
        top_k=40,
        content=f"{prompt}\n{extracted_text_trunc}",
        location="us-central1",
    )
    logger.log(f"cloud_event_id({event_id}): SUMMARY_COMPLETE", severity="INFO")

    output_filename = f'system-test/{name.replace(".pdf", "")}_summary.txt'
    upload_to_gcs(
        _OUTPUT_BUCKET,
        output_filename,
        summary,
    )
    logger.log(
        f"cloud_event_id({event_id}): SUMMARY_UPLOAD {upload_to_gcs}", severity="INFO"
    )

    # If we have any errors, they'll be caught by the bigquery module
    errors = write_summarization_to_table(
        project_id=_PROJECT_ID,
        dataset_id=_DATASET_ID,
        table_id=_TABLE_ID,
        bucket=bucket,
        filename=output_filename,
        complete_text=extracted_text,
        complete_text_uri=complete_text_filename,
        summary=summary,
        summary_uri=output_filename,
        timestamp=time_created,
    )

    if len(errors) > 0:
        logger.log(
            f"cloud_event_id({event_id}): DB_WRITE_ERROR: {errors}", severity="ERROR"
        )
        return {"errors": errors}

    logger.log(f"cloud_event_id({event_id}): DB_WRITE", severity="INFO")

    return {"summary": summary}
