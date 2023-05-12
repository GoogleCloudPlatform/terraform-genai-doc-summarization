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
# TODO(erschmid): replace PROJECT_ID, MODEL_NAME, TABLE_ID, and DATASET_ID with env vars
PROJECT_ID = 'velociraptor-16p1-dev'
OUTPUT_BUCKET = 'velociraptor-16p1-src'
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
@functions_framework.cloud_event
def entrypoint(cloud_event):
    """Entrypoint for Cloud Function

    Args:
      cloud_event (CloudEvent): an event from EventArc

    Returns:
      dictionary with 'summary' and 'output_filename' keys
    """

    event_id = cloud_event["id"]
    bucket = cloud_event.data["bucket"]
    name = cloud_event.data["name"]
    timeCreated = coerce_datetime_zulu(cloud_event.data["timeCreated"])
    orig_pdf_uri = f"gs://{bucket}/{name}"

    logging_client = logging.Client()
    logger = logging_client.logger(FUNCTIONS_GCS_EVENT_LOGGER)
    logger.log(f"cloud_event_id({event_id}): UPLOAD {orig_pdf_uri}",
               severity="INFO")

   

    extracted_text = async_document_extract(bucket, name,
                                            output_bucket=OUTPUT_BUCKET)

    logger.log(f"cloud_event_id({event_id}): OCR  gs://{bucket}/{name}",
               severity="INFO")

    complete_text_filename = f'summaries/{name.replace(".pdf", "")}_fulltext.txt'
    upload_to_gcs(
        OUTPUT_BUCKET,
        complete_text_filename,
        extracted_text,
    )

    logger.log(f"cloud_event_id({event_id}): OCR_UPLOAD {orig_pdf_uri}",
               severity="INFO")

    # TODO(erschmid): replace truncate with better solution
    extracted_text_ = truncate_complete_text(extracted_text)
    summary = predict_large_language_model(
        project_id=PROJECT_ID,
        model_name=MODEL_NAME,
        temperature=0.2,
        max_decode_steps=1024,
        top_p=0.8,
        top_k=40,
        content=f'Summarize:\n{extracted_text_}',
        location="us-central1",
    )

    logger.log(f"cloud_event_id({event_id}): SUMMARY {orig_pdf_uri}",
               severity="INFO")

    output_filename = f'system-test/{name.replace(".pdf", "")}_summary.txt'
    upload_to_gcs(
        OUTPUT_BUCKET,
        output_filename,
        summary,
    )

    logger.log(f"cloud_event_id({event_id}): SUMMARY_UPLOAD {orig_pdf_uri}",
               severity="INFO")

    # If we have any errors, they'll be caught by the bigquery module
    errors = write_summarization_to_table(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        table_id=TABLE_ID,
        bucket=bucket,
        filename=output_filename,
        complete_text=extracted_text,
        complete_text_uri=complete_text_filename,
        summary=summary,
        summary_uri=output_filename,
        timestamp=timeCreated       
    )

    logger.log(f"cloud_event_id({event_id}): DB_WRITE  {orig_pdf_uri}",
               severity="INFO")

    return errors
