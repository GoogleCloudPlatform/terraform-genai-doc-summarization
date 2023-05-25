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
import json
import os
import re

from cloudevents.http import CloudEvent
import functions_framework
from google.auth import default
import vertexai
from vertexai.preview.language_models import TextGenerationModel

_PROJECT_ID = os.environ['PROJECT_ID']
_LOCATION = os.environ['LOCATION']
_CREDENTIALS, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])

_MOCK_TEXT = '''
The efficient-market hypothesis (EMH) is a hypothesis in financial \
economics that states that asset prices reflect all available \
information. A direct implication is that it is impossible to \
"beat the market" consistently on a risk-adjusted basis since market \
prices should only react to new information. Because the EMH is \
formulated in terms of risk adjustment, it only makes testable \
predictions when coupled with a particular model of risk. As a \
result, research in financial economics since at least the 1990s has \
focused on market anomalies, that is, deviations from specific \
models of risk. The idea that financial market returns are difficult \
to predict goes back to Bachelier, Mandelbrot, and Samuelson, but \
is closely associated with Eugene Fama, in part due to his \
influential 1970 review of the theoretical and empirical research. \
The EMH provides the basic logic for modern risk-based theories of \
asset prices, and frameworks such as consumption-based asset pricing \
and intermediary asset pricing can be thought of as the combination \
of a model of risk with the EMH. Many decades of empirical research \
on return predictability has found mixed evidence. Research in the \
1950s and 1960s often found a lack of predictability (e.g. Ball and \
Brown 1968; Fama, Fisher, Jensen, and Roll 1969), yet the \
1980s-2000s saw an explosion of discovered return predictors (e.g. \
Rosenberg, Reid, and Lanstein 1985; Campbell and Shiller 1988; \
Jegadeesh and Titman 1993). Since the 2010s, studies have often \
found that return predictability has become more elusive, as \
predictability fails to work out-of-sample (Goyal and Welch 2008), \
or has been weakened by advances in trading technology and investor \
learning (Chordia, Subrahmanyam, and Tong 2014; McLean and Pontiff \
2016; Martineau 2021).
'''.strip()

_DEFAULT_PARAMETERS = {
    "temperature": .2,
    "max_output_tokens": 256,
    "top_p": .95,
    "top_k": 40,
}


def coerce_datetime_zulu(input_datetime: str) -> datetime.datetime:

    regex = re.compile(r"(.*)(Z$)")
    regex_match = regex.search(input_datetime)
    if regex_match:
        assert input_datetime.startswith(regex_match.group(1))
        assert input_datetime.endswith(regex_match.group(2))
        return datetime.datetime.fromisoformat(f'{input_datetime[:-1]}+00:00')
    raise RuntimeError(
        'The input datetime is not in the expected format. '
        'Please check the format of the input datetime. Expected "Z" at the end'
    )


def default_marshaller(o: object) -> str:
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return str(o)


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
        'Summary:',
        **final_parameters,
    )
    print(f"Response from Model: {response.text}")

    return response.text


@functions_framework.cloud_event
def entrypoint(request: CloudEvent) -> dict[str, str]:

    metadata = dict(
        event_id=request["id"],
        event_type=request["type"],
        bucket=request.data["bucket"],
        name=request.data["name"],
        metageneration=request.data["metageneration"],
        timeCreated=coerce_datetime_zulu(request.data["timeCreated"]),
        updated=coerce_datetime_zulu(request.data["updated"]),
    )

    try:
        response = {
            'revision': os.environ['REVISION'],
            'summary': summarize_text(_MOCK_TEXT),
        }
    except Exception as e:
        response = {
            'exception': str(e),
        }
    response['metadata'] = metadata

    print(json.dumps({'response': response}, indent=2, sort_keys=True, default=default_marshaller))

    return response
