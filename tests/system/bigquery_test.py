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

from src.bigquery import write_summarization_to_table

DATASET_ID = "academic_papers"
TABLE_ID = "summarizations"
PROJECT_ID = os.environ["PROJECT_ID"] 


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def test_write_summarization_to_table(capsys):
    errors = write_summarization_to_table(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        table_id=TABLE_ID,
        bucket="gs://fake_bucket",
        filename="fake.pdf",
        complete_text="This is fake text of an academic paper",
        complete_text_uri="gs://fake_bucket/texts/fake.txt",
        summary="Some fake text summary",
        summary_uri="gs://fake_bucket/fake-summary.txt",
        timestamp=datetime.datetime.now(),
    )

    assert len(errors) == 0
