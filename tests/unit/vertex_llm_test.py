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

from google.cloud import aiplatform
from vertexai.preview.language_models import TextGenerationModel
from unittest.mock import MagicMock, PropertyMock, patch

from src.vertex_llm import predict_large_language_model

@patch.object(aiplatform, 'init')
@patch.object(TextGenerationModel, 'from_pretrained')
def test_predict_large_language_model(mock_get_model, mock_init):
    project_id = 'fake-project'
    model_name = 'fake@fake-orca'
    temperature=0.2
    max_decode_steps=1024
    top_p=0.8
    top_k=40
    content=f'Summarize:\nAbstract: fake\nConclusion: it is faked\n'
    location='us-central1'
    want = 'This is a fake summary'

    mock_response = MagicMock()
    mock_prop = PropertyMock(return_value=want)
    type(mock_response).text = mock_prop
    mock_model = MagicMock(spec=TextGenerationModel)
    mock_model.predict.return_value = mock_response
    mock_get_model.return_value = mock_model

    # Act
    got = predict_large_language_model(project_id,
                                       model_name,
                                       temperature,
                                       max_decode_steps,
                                       top_p,
                                       top_k,
                                       content,
                                       location)
    
    # Assert
    assert want in got
    mock_init.assert_called_with(project=project_id, location=location)    
    mock_model.predict.assert_called_with(content,
                                          temperature=temperature,
                                          max_output_tokens=max_decode_steps,
                                          top_k=top_k,
                                          top_p=top_p)