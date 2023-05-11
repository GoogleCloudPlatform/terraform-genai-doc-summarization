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

import json
import re
from google.cloud import vision
from google.cloud import storage


def async_document_extract(
    bucket: str,
    name: str,
    timeout: int = 420,
):
    """Perform OCR with PDF/TIFF as source files on GCS.

    Original sample is here:
    https://github.com/GoogleCloudPlatform/python-docs-samples/blob/main/vision/snippets/detect/detect.py#L806

    Note: This function can cause the IOPub data rate to be exceeded on a
    Jupyter server. This rate can be changed by setting the variable
    `--ServerApp.iopub_data_rate_limit

    Args:
        bucket (str): GCS URI of the bucket containing the PDF/TIFF files.
        name (str): Name of the PDF/TIFF file.
        timeout (int): Timeout in seconds for the request.


    Returns:
        tuple: (text, gcs_output_path)
    """

    gcs_source_uri = f'gs://{bucket}/{name}'
    file_stem = name.split('.')
    gcs_destination_uri = f'gs://{bucket}/{file_stem[-2]}/'
    gcs_output_path = f'gs://{bucket}/{file_stem[-2]}/complete_text.txt'
    mime_type = 'application/pdf'
    batch_size = 2

    # Perform Vision OCR
    client = vision.ImageAnnotatorClient()

    feature = vision.Feature(
        type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(
        gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size)

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config,
        output_config=output_config)

    operation = client.async_batch_annotate_files(
        requests=[async_request])

    print('Waiting for the operation to finish.')
    operation.result(timeout=timeout)

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client()

    match = re.match(r'gs://([^/]+)/(.+)', gcs_destination_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)

    bucket = storage_client.get_bucket(bucket_name)

    # List objects with the given prefix, filtering out folders.
    blob_list = [blob for blob in list(bucket.list_blobs(
        prefix=prefix)) if not blob.name.endswith('/')]

    # Concatenate all text from the blobs
    complete_text = ""
    for output in blob_list:

        json_string = output.download_as_bytes().decode("utf-8")
        response = json.loads(json_string)

        # The actual response for the first page of the input file.
        page_response = response['responses'][0]
        annotation = page_response['fullTextAnnotation']

        complete_text = complete_text + annotation['text']

    blob = bucket.blob(gcs_output_path)
    blob.upload_from_string(complete_text)

    return (complete_text, gcs_output_path)
