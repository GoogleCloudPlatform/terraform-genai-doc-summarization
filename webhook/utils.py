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

ABSTRACT_LENGTH = 150 * 10  # Abstract recommended max word length * avg 10 letters long
CONCLUSION_LENGTH = 200 * 10  # Conclusion max word legnth * avg 10 letters long
ABSTRACT_H1 = "abstract"
CONCLUSION_H1 = "conclusion"


def coerce_datetime_zulu(input_datetime: datetime.datetime):
    """Force datetime into specific format.

    Args:
      input_datetime (datetime.datetime): the datetime to coerce

    """
    regex = re.compile(r"(.*)(Z$)")
    regex_match = regex.search(input_datetime)
    if regex_match:
        assert input_datetime.startswith(regex_match.group(1))
        assert input_datetime.endswith(regex_match.group(2))
        return datetime.datetime.fromisoformat(f"{input_datetime[:-1]}+00:00")
    raise RuntimeError(
        "The input datetime is not in the expected format. "
        'Please check format of the input datetime. Expected "Z" at the end'
    )


def clean_text(original_text: str) -> str:
    """Extracts the abstract and conclusion from an academic paper.

    Uses a heuristics to approximate the extent of the abstract and conclusion.
    For abstract: assumes beginning after the string `abstract` and extends for 6-7 sentences
    For conclusion: assumes beginning after the string `conclusion` and extends for 7-9 sentences

    Args:
        complete_text (str): the complete text of the academic paper

    Returns
        str: the truncated paper
    """
    clean_text = original_text.lower()

    return f"""
    Text: {clean_text}
    """