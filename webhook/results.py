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


_PROJECT_ID = os.environ['PROJECT_ID']
_LOCATION = os.environ['LOCATION']
_MODEL_NAME = 'text-bison@001'
_DEFAULT_PARAMETERS = {
    "temperature": .2,
    "max_output_tokens": 256,
    "top_p": .95,
    "top_k": 40,
}

def compare_results(
    question: str, parameters: None | dict[str, int | float] = None, model_display_name: str = "A_TUNED_MODEL",
) -> list:
  """Compare tuned and original results.

  Args:
    question: Question to ask.
    model_display_name: Model display name.

  Returns:
    A list of responses and tuned responses.
  """
  vertexai.init(
      project=_PROJECT_ID,
      location=_LOCATION,
  )

  final_parameters = _DEFAULT_PARAMETERS.copy()
  if parameters:
      final_parameters.update(parameters)

  model = TextGenerationModel.from_pretrained("_MODEL_NAME")
  tuned_model = model.get_tuned_model("projects/801452371447/locations/us-central1/models/836220374365503488")

  response = model.predict(question, **final_parameters,)
  tuned_response = (tuned_model.predict("What are qubits?"))

  print("Here is the question: What are qubits?")
  print("***************************************")
  print(f"Here is the original response: {response.text}")
  print("***************************************")
  print(f"Here is the tuned response: {tuned_response.text}")

  return [response, tuned_response]