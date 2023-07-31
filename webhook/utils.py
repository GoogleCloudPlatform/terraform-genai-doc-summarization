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

from google.cloud import logging
import datetime
import re

ABSTRACT_LENGTH = 150 * 8  # Abstract recommended max word length * avg 8 letters long
CONCLUSION_LENGTH = 200 * 8  # Conclusion max word length * avg 8 letters long
ABSTRACT_H1 = "abstract"
CONCLUSION_H1 = "conclusion"

CONTENT_ERROR_MESSAGE = """
Uploaded PDF doesn't contain an abstract or conclusion paragraph. The
document summarization pipeline will attempt a best effort at summarizing
the PDF. Your results might vary in quality.

For best results, use a single-column, academic paper that contains both
a labeled 'Abstract' and 'Conclusion' section.
"""


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


def truncate_complete_text(complete_text: str, logger_name: str) -> str:
    """Extracts the abstract and conclusion from an academic paper.

    Uses a heuristics to approximate the extent of the abstract and conclusion.
    For abstract: assumes beginning after the string `abstract` and extends for 6-7 sentences
    For conclusion: assumes beginning after the string `conclusion` and extends for 7-9 sentences

    #56 : Improve this function

    Args:
        complete_text (str): the complete text of the academic paper

    Returns
        str: the truncated paper
    """
    complete_text = complete_text.lower()
    abstract_start = complete_text.find(ABSTRACT_H1)

    # If no "Abstract" heading found, produce the entire text
    if abstract_start == -1:
        abstract_start = 0
        log_content_error(logger_name=logger_name)

    conclusion_start = complete_text.find(CONCLUSION_H1)

    # If no "Conclusion" heading found, produce the last little bit
    # of the text
    if conclusion_start == -1:
        conclusion_start = len(complete_text) - (CONCLUSION_LENGTH)
        log_content_error(logger_name=logger_name)

    abstract = complete_text[abstract_start:ABSTRACT_LENGTH]
    conclusion = complete_text[conclusion_start:]
    if len(conclusion) > CONCLUSION_LENGTH:
        conclusion = conclusion[:CONCLUSION_LENGTH]

    return f"""
    Abstract: {abstract}

    Conclusion: {conclusion}
    """


def log_content_error(logger_name: str):
    logging_client = logging.Client()
    logger = logging_client.logger(logger_name)
    logger.log(CONTENT_ERROR_MESSAGE, severity="WARNING")
