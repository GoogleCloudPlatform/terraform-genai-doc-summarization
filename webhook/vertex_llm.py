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

from vertexai.preview.language_models import TextGenerationModel
import vertexai


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
      temperature (float): controls the randomness of predictions
      max_decode_steps (int): the maximum number of decode steps
      top_p (float): cumulative probability of parameter highest vocabulary tokens
      top_k (int): number of highest propbability vocabulary tokens to keep for top-k-filtering
      content (str): the text to summarize
      location (str): the Google Cloud region to run in
      tuned_model_name (str): the LLM model to use

    Returns:
      The summarization of the content
    """
    vertexai.init(
        project=project_id,
        location=location,
    )

    model = TextGenerationModel.from_pretrained(model_name)
    if tuned_model_name:
        model = model.get_tuned_model(tuned_model_name)
    response = model.predict(
        content,
        temperature=temperature,
        max_output_tokens=max_decode_steps,
        top_k=top_k,
        top_p=top_p,
    )
    return response.text
