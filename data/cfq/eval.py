# coding=utf-8
# Copyright 2020 The Google Research Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Grade CFQ output using the original canonical query format.

This adapter keeps the two upstream preprocessing functions and adds chat
prompting and output extraction for Benchopedia.
"""

import re
import string


ATTEMPTS = 2
MODEL_OPTIONS = {"reasoning": {"enabled": False}}
CAPTURE_FILES = ("apache-2.0.txt",)
FENCE = re.compile(r"\x60{3}(?:sparql)?[ \t]*\n(.*?)\n\x60{3}", re.IGNORECASE | re.DOTALL)
QUERY = re.compile(r"SELECT\b.*\bWHERE\s*\{.+\}", re.IGNORECASE)

# https://github.com/google-research/google-research/blob/675101293d39a5b88996e58475a026e039a0bdae/cfq/preprocess.py#L31-L51
def tokenize_punctuation(text):
  text = map(lambda c: ' %s ' % c if c in string.punctuation else c, text)
  return ' '.join(''.join(text).split())


def preprocess_sparql(query):
  """Do various preprocessing on the SPARQL query."""
  # Tokenize braces.
  query = query.replace('count(*)', 'count ( * )')

  tokens = []
  for token in query.split():
    # Replace 'ns:' prefixes.
    if token.startswith('ns:'):
      token = token[3:]
    # Replace mid prefixes.
    if token.startswith('m.'):
      token = 'm_' + token[2:]
    tokens.append(token)

  return ' '.join(tokens).replace('\\n', ' ')


def messages(task):
    return [{"role": "user", "content": (
        f"{task['prompt']}\n\n"
        "Translate the question into a Freebase SPARQL query in the CFQ format. "
        "Keep the input entity placeholders, such as M0 and M1. Use ?x0, ?x1, and so on for variables. "
        "Return only the SELECT query."
    )}]


def grade(task, output):
    reply = output.strip()
    block = FENCE.fullmatch(reply)
    answer = preprocess_sparql(block[1] if block else reply)
    if not QUERY.fullmatch(answer):
        return "unparseable", None
    return ("pass" if answer == task["solution"] else "fail"), answer
