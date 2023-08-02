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
import os

from vertexai.preview.language_models import TextGenerationModel
import vertexai

def extract_questions(
    project_id: str,
    model_name: str,
    temperature: float,
    max_decode_steps: int,
    top_p: float,
    top_k: int,
    text: str,
    location: str = "us-central1",
) -> str:
    """Predict using a Large Language Model.

    Args:
      project_id (str): the Google Cloud project ID
      model_name (str): the name of the LLM model to use
      temperature (float): controls the randomness of predictions
      max_decode_steps (int): TODO(nicain)
      top_p (float): cumulative probability of parameter highest vocabulary tokens
      top_k (int): number of highest propbability vocabulary tokens to keep for top-k-filtering
      text (str): the text to summarize
      location (str): the Google Cloud region to run in

    Returns:
      The summarization of the content
    """
    vertexai.init(
        project=project_id,
        location=location,
    )
    print("*******Bison Language model initialized*******", vertexai.init)
    model = TextGenerationModel.from_pretrained(model_name)
    print("This is the text for tuning"+text)
    response = model.predict(
        f"Extract at least 20 Questions based on the following article: {text}\nQuestions:",
        temperature=temperature,
        max_output_tokens=max_decode_steps,
        top_k=top_k,
        top_p=top_p
    )
    question_list = response.text.splitlines( )
    print(f"Response from Model: {question_list}")

    return question_list


def tuning_dataset(
    project_id: str,
    model_name: str,
    temperature: float,
    max_decode_steps: int,
    top_p: float,
    top_k: int,
    text: str,
    location: str = "us-central1",
    tuned_model_name: str = "",
) -> list[dict]:
    """Extraction Example with a Large Language Model"""
    question_list = extract_questions(
        project_id=project_id,
        model_name=model_name,
        temperature=0.2,
        max_decode_steps=1024,
        top_p=0.8,
        top_k=40,
        text=text,
        location="us-central1",
    )

    vertexai.init(
        project=project_id,
        location=location,
    )
    print("*******Bison Language model initialized*******", vertexai.init)

    model = TextGenerationModel.from_pretrained(model_name)
    tuning_data = []
    for question in question_list:
      response = model.predict(
          f'Answer the following question based on the text: {text}\n'
          f'Question: {question}\n Answer:',
          temperature=temperature,
          max_output_tokens=max_decode_steps,
          top_k=top_k,
          top_p=top_p,
      )
      tuning_data.append({"input_text": question, "output_text": response.text})
    print(f"Here is the generated tuning dataset from the given text: {tuning_data}")

    return tuning_data


def tuning(
    credentials,
    project_id: str,
    model_name: str,
    temperature: float,
    max_decode_steps: int = 1024,
    top_p: float = 0.8,
    top_k: int = 40,
    text: str = None,
    location: str = "us-central1",
    tuned_model_name: str = "",
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
    import pandas as pd

    vertexai.init(
        project=project_id,
        location=location,
        credentials=credentials
    )
    model = TextGenerationModel.from_pretrained("google/text-bison@001")

    jsonl_dataset = tuning_dataset(
        project_id=project_id,
        model_name=model_name,
        temperature=0.2,
        max_decode_steps=max_decode_steps,
        top_p=top_p,
        top_k=top_k,
        text=text,
        location="us-central1",
    )
    model.tune_model(
        training_data=pd.DataFrame(data=jsonl_dataset),
        # Optional:
        train_steps=10,
        tuning_job_location="europe-west4",  # Only supported in europe-west4 for Public Preview
        tuned_model_location=location,
    )

    print(model._job.status)
    return jsonl_dataset
