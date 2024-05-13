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

import json
import os
import pprint
import subprocess
from collections.abc import Iterator
from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest
from google.cloud import bigquery

from main import process_document

PROJECT_ID = os.environ["PROJECT_ID"]


def run_cmd(*cmd: str, **kwargs: Any) -> subprocess.CompletedProcess:
    """Run a command in a subprocess.

    Args:
        *cmd: The command to run.
        **kwargs: Additional keyword arguments to pass to subprocess.run().

    Returns:
        The completed subprocess.
    """
    print(f">> {cmd}")
    return subprocess.run(cmd, check=True, **kwargs)


@pytest.fixture(scope="session")
def terraform_outputs() -> Iterator[dict[str, str]]:
    """Yield the Terraform outputs.

    Yields:
        The Terraform outputs as a dictionary.
    """
    print("---")
    print(f"{PROJECT_ID=}")
    if not os.environ.get("TEST_SKIP_TERRAFORM"):
        run_cmd("terraform", "-chdir=..", "init", "-input=false")
        run_cmd(
            "terraform",
            "-chdir=..",
            "apply",
            "-input=false",
            "-auto-approve",
            f"-var=project_id={PROJECT_ID}",
            "-var=unique_names=true",
            "-target=google_storage_bucket.main",
            "-target=google_document_ai_processor.ocr",
            "-target=google_bigquery_table.main",
        )
    p = run_cmd("terraform", "-chdir=..", "output", "-json", stdout=subprocess.PIPE)
    outputs = {name: value["value"] for name, value in json.loads(p.stdout.decode("utf-8")).items()}
    print(f"{PROJECT_ID=}")
    print(f"outputs:\n{pprint.pformat(outputs)}")
    yield outputs
    if not os.environ.get("TEST_SKIP_TERRAFORM"):
        run_cmd(
            "terraform",
            "-chdir=..",
            "destroy",
            "-input=false",
            "-auto-approve",
            f"-var=project_id={PROJECT_ID}",
        )


def test_end_to_end(terraform_outputs: dict[str, str]) -> None:
    """End-to-end test.

    Args:
        terraform_outputs: The Terraform outputs.
    """
    output_bucket = terraform_outputs["bucket_main_name"]
    docai_processor_id = terraform_outputs["documentai_processor_id"]
    bq_dataset = terraform_outputs["bigquery_dataset_id"]
    bq_table = "summaries"

    print(">> process_document")
    process_document(
        event_id=f"webhook-test-{uuid4().hex[:6]}",
        input_bucket="arxiv-dataset",
        filename="arxiv/cmp-lg/pdf/9410/9410009v1.pdf",
        mime_type="application/pdf",
        time_uploaded=datetime.now(),
        docai_processor_id=docai_processor_id,
        docai_location="us",
        output_bucket=output_bucket,
        bq_dataset=bq_dataset,
        bq_table=bq_table,
    )

    # Make sure we have a non-empty dataset.
    print(">> Checking bigquery table")
    bq_client = bigquery.Client()
    rows = bq_client.list_rows(bq_client.get_table(f"{bq_dataset}.{bq_table}"))
    assert len(list(rows)) > 0
