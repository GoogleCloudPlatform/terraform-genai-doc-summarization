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
import re
import os
from typing import Union
import pandas as pd

from google.auth import default
import vertexai
from vertexai.preview.language_models import TextGenerationModel

_FUNCTIONS_GCS_EVENT_LOGGER = 'function-triggered-by-storage'
_FUNCTIONS_VERTEX_EVENT_LOGGER = 'summarization-by-llm'

from bigquery import write_summarization_to_table
from document_extract import async_document_extract
from storage import upload_to_gcs
from vertex_llm import predict_large_language_model
from utils import coerce_datetime_zulu, truncate_complete_text

_MOCK_DATA = [{'input_text': 'What has research in financial economics since at least the 1990s focused on?',
  'output_text': 'market anomalies'},
 {'input_text': 'What is the direct implication of the efficient-market hypothesis?',
  'output_text': 'it is impossible to "beat the market" consistently on a risk-adjusted basis'},
 {'input_text': 'What is the EMH formulated in terms of?',
  'output_text': 'risk adjustment'},
 {'input_text': 'What is the result of research in financial economics since at least the 1990s?',
  'output_text': 'market anomalies'},
 {'input_text': 'Who is the idea that financial market returns are difficult to predict associated with?',
  'output_text': 'Eugene Fama'},
 {'input_text': 'What does the EMH provide the basic logic for?',
  'output_text': 'modern risk-based theories of asset prices'},
 {'input_text': 'What are some examples of return predictors?',
  'output_text': 'Rosenberg, Reid, and Lanstein 1985; Campbell and Shiller 1988; Jegadeesh and Titman 1993'},
 {'input_text': 'What has been found since the 2010s?',
  'output_text': 'return predictability has become more elusive'},
 {'input_text': 'Who is Eugene Fama?',
  'output_text': 'an influential 1970 review of the theoretical and empirical research'},
 {'input_text': 'Who is closely associated with the efficient-market hypothesis?',
  'output_text': 'Eugene Fama'}]

_DEFAULT_PARAMETERS = {
    "temperature": .2,
    "max_output_tokens": 256,
    "top_p": .95,
    "top_k": 40,
}
_DATASET_ID = os.environ['DATASET_ID']
_TABLE_ID = os.environ['TABLE_ID']


def default_marshaller(o: object) -> str:
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return str(o)


def generate_questions(text: str, parameters: None | dict[str, int | float] = None) -> str:
    """Generate sample questions with a Large Language Model"""
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
      f'Extract at least 10 Questions based on the following article:'
    , **final_parameters)
    print(f"Questions generated from Model: {response.text}")

    return response.text


def question_answering(text: str, parameters: None | dict[str, int | float] = None) -> str:
    """Answer the extracted questions with a Large Language Model"""
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
      f'{text}\n'
      'Answer the following questions one by one:\n'
      'What is the direct implication of the efficient-market hypothesis?\n'
      'What is the EMH formulated in terms of?\n'
      'What is the result of research in financial economics since at least the 1990s?\n'
      'Who is the idea that financial market returns are difficult to predict associated with?\n'
      'What does the EMH provide the basic logic for?\n'
      'What are some examples of return predictors?\n'
      'What has been found since the 2010s?\n'
      'Who is Eugene Fama?\n'
      'Who is closely associated with the efficient-market hypothesis?\n'
      'What has research in financial economics since at least the 1990s focused on?\n'
      'Answer1:\n'
      'Answer2:\n'
      'Answer3:\n'
      'Answer4:\n'
      'Answer5:\n'
      'Answer6:\n'
      'Answer7:\n'
      'Answer8:\n'
      'Answer9:\n'
      'Answer10:\n'
    , **final_parameters)
    print(f"Answers of extractive questions from Model: {response.text}")

credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
def tuning(
    project_id: str,
    location: str,
    training_data: pd.DataFrame | str,
    train_steps: int = 10,
) -> None:
    """Tune a new model, based on a prompt-response data.

    "training_data" can be either the GCS URI of a file formatted in JSONL format
    (for example: training_data=f'gs://{bucket}/{filename}.jsonl'), or a pandas
    DataFrame. Each training example should be JSONL record with two keys, for
    example:
      {
        "input_text": <input prompt>,
        "output_text": <associated output>
      },
    or the pandas DataFame should contain two columns:
      ['input_text', 'output_text']
    with rows for each training example.

    Args:
      project_id: GCP Project ID, used to initialize vertexai
      location: GCP Region, used to initialize vertexai
      training_data: GCS URI of jsonl file or pandas dataframe of training data
      train_steps: Number of training steps to use when tuning the model.
    """
    vertexai.init(
        project=project_id,
        location=location,
        credentials=credentials
    )
    model = TextGenerationModel.from_pretrained("google/text-bison@001")

    model.tune_model(
        training_data=training_data,
        # Optional:
        train_steps=train_steps,
        tuning_job_location="europe-west4",  # Only supported in europe-west4 for Public Preview
        tuned_model_location=location,
    )

    print(model._job.status)
    return model

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
      'Summary:'
    , **final_parameters)
    print(f"Response from Model: {response.text}")

    return response.text

# WEBHOOK FUNCTION
# @functions_framework.cloud_request
def entrypoint(request):
    """Entrypoint for Cloud Function"""

    print(request.get_json())
    return "HelloWorld!!!!"

# @functions_framework.cloud_event
# def entrypoint(request):

#   metadata = dict(
#     event_id = request["id"],
#     event_type = request["type"],
#     bucket = request.data["bucket"],
#     name = request.data["name"],
#     metageneration = request.data["metageneration"],
#     timeCreated = coerce_datetime_zulu(request.data["timeCreated"]),
#     updated = coerce_datetime_zulu(request.data["updated"]),
#   )

#   try:
#     response = {
#       'revision': os.environ['REVISION'],
#       'questions': generate_questions(_MOCK_TEXT),
#       'answers': question_answering(_MOCK_TEXT),
#       'tuning': tune_model(_MOCK_DATA),
#       'summary': summarize_text(_MOCK_TEXT),
#     }
#   except Exception as e:
#     response = {
#       'exception': str(e),
#     }
#   response['metadata'] = metadata


  
#   print(json.dumps({'response': response}, indent=2, sort_keys=True, default=default_marshaller))

#   return response