# Copyright 2024 Google LLC
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

import logging
import os
from collections.abc import Iterator
from datetime import datetime

import functions_framework
from cloudevents.http import CloudEvent
from google.api_core.client_options import ClientOptions
from google.cloud import documentai
from google.cloud import bigquery
from google.cloud import storage  # type: ignore
from vertexai.preview.generative_models import GenerativeModel  # type: ignore

SUMMARIZATION_PROMPT = """\
Give me a summary of the following text.
Use simple language and give examples.
Explain to an undergraduate.

TEXT:
{text}
"""


@functions_framework.cloud_event
def on_cloud_event(event: CloudEvent) -> None:
    """Process a new document from an Eventarc event.

    Args:
        event: CloudEvent object.
    """
    try:
        process_document(
            event_id=event.data["id"],
            input_bucket=event.data["bucket"],
            filename=event.data["name"],
            mime_type=event.data["contentType"],
            time_uploaded=datetime.fromisoformat(event.data["timeCreated"]),
            docai_processor_id=os.environ["DOCAI_PROCESSOR"],
            docai_location=os.environ.get("DOCAI_LOCATION", "us"),
            output_bucket=os.environ["OUTPUT_BUCKET"],
            bq_dataset=os.environ["BQ_DATASET"],
            bq_table=os.environ["BQ_TABLE"],
        )
    except Exception as e:
        logging.exception(e, stack_info=True)


def process_document(
    event_id: str,
    input_bucket: str,
    filename: str,
    mime_type: str,
    time_uploaded: datetime,
    docai_processor_id: str,
    docai_location: str,
    output_bucket: str,
    bq_dataset: str,
    bq_table: str,
):
    """Process a new document.

    Args:
        event_id: ID of the event.
        input_bucket: Name of the input bucket.
        filename: Name of the input file.
        mime_type: MIME type of the input file.
        time_uploaded: Time the input file was uploaded.
        docai_processor_id: ID of the Document AI processor.
        docai_location: Location of the Document AI processor.
        output_bucket: Name of the output bucket.
        bq_dataset: Name of the BigQuery dataset.
        bq_table: Name of the BigQuery table.
    """
    doc_path = f"gs://{input_bucket}/{filename}"
    print(f"📖 {event_id}: Getting document text")
    doc_text = "\n".join(
        get_document_text(
            doc_path,
            mime_type,
            docai_processor_id,
            output_bucket,
            docai_location,
        )
    )

    model_name = "gemini-pro"
    print(f"📝 {event_id}: Summarizing document with {model_name}")
    print(f"  - Text length:    {len(doc_text)} characters")
    doc_summary = generate_summary(doc_text, model_name)
    print(f"  - Summary length: {len(doc_summary)} characters")

    print(f"🗃️ {event_id}: Writing document summary to BigQuery: {bq_dataset}.{bq_table}")
    write_to_bigquery(
        event_id=event_id,
        time_uploaded=time_uploaded,
        doc_path=doc_path,
        doc_text=doc_text,
        doc_summary=doc_summary,
        bq_dataset=bq_dataset,
        bq_table=bq_table,
    )

    print(f"✅ {event_id}: Done!")


def get_document_text(
    input_file: str,
    mime_type: str,
    processor_id: str,
    temp_bucket: str,
    docai_location: str = "us",
) -> Iterator[str]:
    """Perform Optical Character Recognition (OCR) with Document AI on a Cloud Storage file.

    For more information, see:
        https://cloud.google.com/document-ai/docs/process-documents-ocr

    Args:
        input_file: GCS URI of the document file.
        mime_type: MIME type of the document file.
        processor_id: ID of the Document AI processor.
        temp_bucket: GCS bucket to store Document AI temporary files.
        docai_location: Location of the Document AI processor.

    Yields: The document text chunks.
    """
    # You must set the `api_endpoint` if you use a location other than "us".
    documentai_client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(api_endpoint=f"{docai_location}-documentai.googleapis.com")
    )

    # We're using batch_process_documents instead of process_document because
    # process_document has a quota limit of 15 pages per document, while
    # batch_process_documents has a quota limit of 500 pages per request.
    #   https://cloud.google.com/document-ai/quotas#general_processors
    operation = documentai_client.batch_process_documents(
        request=documentai.BatchProcessRequest(
            name=processor_id,
            input_documents=documentai.BatchDocumentsInputConfig(
                gcs_documents=documentai.GcsDocuments(
                    documents=[
                        documentai.GcsDocument(gcs_uri=input_file, mime_type=mime_type),
                    ],
                ),
            ),
            document_output_config=documentai.DocumentOutputConfig(
                gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
                    gcs_uri=f"gs://{temp_bucket}/ocr/{input_file.split('gs://')[-1]}",
                ),
            ),
        ),
    )
    operation.result()

    # Read the results of the Document AI operation from Cloud Storage.
    storage_client = storage.Client()
    metadata = documentai.BatchProcessMetadata(operation.metadata)
    output_gcs_path = metadata.individual_process_statuses[0].output_gcs_destination
    (output_bucket, output_prefix) = output_gcs_path.removeprefix("gs://").split("/", 1)
    for blob in storage_client.list_blobs(output_bucket, prefix=output_prefix):
        blob_contents = blob.download_as_bytes()
        document = documentai.Document.from_json(blob_contents, ignore_unknown_fields=True)
        yield document.text


def generate_summary(text: str, model_name: str = "gemini-pro") -> str:
    """Generate a summary of the given text.

    Args:
        text: The text to summarize.
        model_name: The name of the model to use for summarization.

    Returns:
        The generated summary.
    """
    model = GenerativeModel(model_name)
    prompt = SUMMARIZATION_PROMPT.format(text=text)
    return model.generate_content(prompt).text


def write_to_bigquery(
    event_id: str,
    time_uploaded: datetime,
    doc_path: str,
    doc_text: str,
    doc_summary: str,
    bq_dataset: str,
    bq_table: str,
) -> None:
    """Write the summary to BigQuery.

    Args:
        event_id: The Eventarc trigger event ID.
        time_uploaded: Time the document was uploaded.
        doc_path: Cloud Storage path to the document.
        doc_text: Text extracted from the document.
        doc_summary: Summary generated fro the document.
        bq_dataset: Name of the BigQuery dataset.
        bq_table: Name of the BigQuery table.
    """
    bq_client = bigquery.Client()
    bq_client.insert_rows(
        table=bq_client.get_table(f"{bq_dataset}.{bq_table}"),
        rows=[
            {
                "event_id": event_id,
                "time_uploaded": time_uploaded,
                "time_processed": datetime.now(),
                "document_path": doc_path,
                "document_text": doc_text,
                "document_summary": doc_summary,
            },
        ],
    )
