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

import backoff
import datetime
import os

from google.cloud import storage

from src.bigquery import write_summarization_to_table
from src.document_extract import async_document_extract
from src.storage import upload_to_gcs
from src.utils import truncate_complete_text
from src.vertex_llm import predict_large_language_model

PROJECT_ID = os.environ["PROJECT_ID"]
BUCKET_NAME = os.environ["BUCKET"]
DATASET_ID = "academic_papers"
TABLE_ID = "summarizations"
FILE_NAME = 'pdfs/9404001v1.pdf'
MODEL_NAME = 'text-bison@001'


def check_blob_exists(bucket, filename) -> bool:
    client = storage.Client()
    bucket = client.bucket(bucket)
    blob = bucket.blob(filename)
    return blob.exists()

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def test_up16_services():
    extracted_text = async_document_extract(BUCKET_NAME, FILE_NAME)

    assert "Abstract" in extracted_text

    complete_text_filename = f'system-test/{FILE_NAME.replace(".pdf", "")}_fulltext.txt'
    upload_to_gcs(
        BUCKET_NAME,
        complete_text_filename,
        extracted_text,
    )

    assert check_blob_exists(BUCKET_NAME, complete_text_filename)

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

    assert summary != ""

    output_filename = f'system-test/{FILE_NAME.replace(".pdf", "")}_summary.txt'
    upload_to_gcs(
        BUCKET_NAME,
        output_filename,
        summary,
    )

    assert check_blob_exists(BUCKET_NAME, output_filename)

    errors = write_summarization_to_table(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        table_id=TABLE_ID,
        bucket=BUCKET_NAME,
        filename=output_filename,
        complete_text=extracted_text,
        complete_text_uri=complete_text_filename,
        summary=summary,
        summary_uri=output_filename,
        timestamp=datetime.datetime.now()        
    )

    assert len(errors) == 0