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

from google import auth
from google.cloud import aiplatform
from vertexai.preview.language_models import TextGenerationModel

import datetime
import requests
from requests.adapters import HTTPAdapter
import urllib3


def predict_large_language_model(
    project_id: str,
    model_name: str,
    temperature: float,
    max_decode_steps: int,
    top_p: float,
    top_k: int,
    content: str,
    location: str = "us-central1",
    tuned_model_name: str = "",
) -> str:
    """Predict using a Large Language Model.

    Args:
      project_id (str): the Google Cloud project ID
      model_name (str): the name of the LLM model to use
      temperature (float): TODO(nicain)
      max_decode_steps (int): TODO(nicain)
      top_p (float): TODO(nicain)
      top_k (int): TODO(nicain)
      content (str): the text to summarize
      location (str): the Google Cloud region to run in
      tuned_model_name (str): TODO(nicain)

    Returns:
      The summarization of the content
    """
    aiplatform.init(project=project_id, location=location)
    model = TextGenerationModel.from_pretrained(model_name)
    if tuned_model_name:
        model = model.get_tuned_model(tuned_model_name)
    response = model.predict(
        content,
        temperature=temperature,
        max_output_tokens=max_decode_steps,
        top_k=top_k,
        top_p=top_p,)
    return response.text


def predict_large_language_model_hack(
    project_id: str,
    model_name: str,
    temperature: float,
    max_decode_steps: int,
    top_p: float,
    top_k: int,
    content: str,
    location: str = "us-central1",
    tuned_model_name: str = "",
) -> str:
    """Predict using a Large Language Model.

    Args:
      project_id (str): the Google Cloud project ID
      model_name (str): the name of the LLM model to use
      temperature (float): TODO(nicain)
      max_decode_steps (int): TODO(nicain)
      top_p (float): TODO(nicain)
      top_k (int): TODO(nicain)
      content (str): the text to summarize
      location (str): the Google Cloud region to run in
      tuned_model_name (str): TODO(nicain)

    Returns:
      The summarization of the content
    """
    credentials, project_id = auth.default()
    request = auth.transport.requests.Request()
    credentials.refresh(request)

    audience = f'https://us-central1-aiplatform.googleapis.com/v1/projects/cloud-large-language-models/locations/us-central1/endpoints/{model_name}:predict'
    s = requests.Session()
    retries = urllib3.util.Retry(
      connect=10,
      read=1,
      backoff_factor=0.1,
      status_forcelist=[429, 500],
    )

    headers = {}
    headers["Content-type"] = "application/json"
    headers["Authorization"] = f"Bearer {credentials.token}"

    json_data = {
      "instances": [
        {"content": content},
      ],
      "parameters": {
        "temperature": temperature,
        "maxDecodeSteps": max_decode_steps,
        "topP": top_p,
        "topK": top_k,
      }
    }

    s.mount('https://', HTTPAdapter(max_retries=retries))
    response = s.post(
        audience,
        headers=headers,
        timeout=datetime.timedelta(minutes=15).total_seconds(),
        json=json_data,
    )

    return response.json()['predictions'][0]['content']
