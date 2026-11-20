# Copyright 2024 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Score all three NATURAL PLAN tasks with the pinned authors' functions.

Benchmark adapter and input loading are specific to Benchopedia. The
per-example upstream scoring functions are preserved below.
https://github.com/google-deepmind/natural-plan/tree/ca76db336072ff8931db43bc1ca8d381038cf073
"""

import collections
import datetime
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ATTEMPTS = 1
CAPTURE_FILES = ("grader-inputs.json.gz",)
GRADER_INPUTS_SHA256 = "8f991a32ab644a55505a1df323e0ee5a1cd69cda8eafe196d9431e18a70b5f44"


@lru_cache(maxsize=1)
def grader_inputs():
    path = Path(__file__).with_name(CAPTURE_FILES[0])
    with gzip.open(path, "rb") as stream:
        payload = stream.read()
    if hashlib.sha256(payload).hexdigest() != GRADER_INPUTS_SHA256:
        raise ValueError(f"Unexpected revision of {path}")
    return json.loads(payload)


def kind_and_data(task):
    key, number = task["key"].rsplit("-", 1)
    kind = key.replace("-", "_")
    return kind, grader_inputs()[f"{kind}_example_{int(number)}"]


def messages(task):
    _, data = kind_and_data(task)
    return [{"role": "user", "content": data[0]}]


def grade(task, output):
    kind, data = kind_and_data(task)
    if not output.strip():
        return "unparseable", None
    if kind == "trip_planning":
        plan = parse_response(output)
        if not plan:
            return "unparseable", None
        passed = compute_example_score(*data[1:], plan) == 1.0
        answer = json.dumps(plan, ensure_ascii=False)
    elif kind == "calendar_scheduling":
        day, start, stop = _parse_response(output)
        if not day:
            return "unparseable", None
        passed = compute_solve_rate([output], [task["solution"]]) == 1.0
        answer = f"{day}, {start:g} - {stop:g}"
    else:
        raw_constraints, distances = data[1:]
        start_location, initial_time = raw_constraints[0]
        constraints = process_constraints(raw_constraints[1:])
        expected = validator_from_text(task["solution"].split("\n"), constraints,
                                       start_location, initial_time, distances)
        plan = parse_text_plan(output)
        if not plan:
            return "unparseable", None
        try:
            actual = validator_from_text(plan, constraints, start_location, initial_time, distances)
        except (IndexError, KeyError, OverflowError):
            return "fail", "Invalid meeting or travel step"
        passed = actual == expected
        answer = f"{actual} valid meetings"
    return ("pass" if passed else "fail"), answer


# trip_planning functions from evaluate_trip_planning.py

def parse_response(response: str):
  """Parse the response.

  Returns a parsed plan in a list of (city, stay_days) tuples.

  Args:
    response: Raw response from the model.

  Returns:
    Structured plan after parsing.
  """
  pattern_visit = r'\d+-\d+'
  pattern_flight = r'.*Day (\d+).*from (\w+) to (\w+)'
  pattern_days = r'European cities for (\d+) days'

  days, flights, flight_days = [], [], []
  total_days = None
  for piece in response.split('\n'):
    days_match = re.findall(pattern_days, piece)
    if days_match:
      total_days = int(days_match[0])

    visit_match = re.findall(pattern_visit, piece)
    if visit_match:
      days.append(visit_match[0])
      end_day = int(visit_match[0].split('-')[1])
      # Reach the end of the plan, stop to avoid parsing alternative plans.
      if end_day == total_days:
        break
    flight_match = re.findall(pattern_flight, piece)
    if flight_match:
      flights.append(flight_match[0])

  visit_cities, parsed_plan = [], []
  for flight_day, begin_city, end_city in flights:
    flight_days.append(int(flight_day))
    if not visit_cities:
      visit_cities.append(begin_city)
      visit_cities.append(end_city)
    else:
      visit_cities.append(end_city)

  if not days or not flights or not visit_cities:
    return []
  last_day = int(days[-1].split('-')[1])
  flight_days = [1] + flight_days + [last_day]
  for i, visit_city in enumerate(visit_cities):
    city_stay = flight_days[i + 1] - flight_days[i] + 1
    parsed_plan.append((visit_city, city_stay))

  return parsed_plan


def compute_example_score(cities: str, durations: str, parsed_plan: list[Any]):
  """Compute the exact-match accuracy.

  Compute the example-level exact_match score (0/1) given the parsed plan
  and the ground truth in the format of durations and cities.

  Args:
    cities: The cities in the plan in the format of "city1**city2**city3".
    durations: The durations of the stay in each city in the format of
      "1**2**3".
    parsed_plan: The parsed plan from the response.

  Returns:
    Exact-match accuracy of 0 (mismatched) or 1 (matched).
  """

  stays = [x for x in cities.split('**') if x]
  days = [int(x) for x in durations.split('**') if x]
  num_stays = min(len(stays), len(parsed_plan))
  num_match = 0
  for i in range(num_stays):
    if stays[i] == parsed_plan[i][0] and days[i] == parsed_plan[i][1]:
      num_match += 1
    else:
      break
  hard_score = 0.0 if num_match / len(stays) < 1.0 else 1.0
  return hard_score


# meeting_planning functions from evaluate_meeting_planning.py

def convert_to_time_obj(time_str: str):
  return datetime.datetime.strptime(time_str, "%I:%M%p")


def process_constraints(data: tuple[Any, ...]):
  contraints = collections.defaultdict(dict)
  for name, location, times, meeting_time in data:
    contraints[name]["location"] = location

    start_time = convert_to_time_obj(times.split("to")[0].strip())
    end_time = convert_to_time_obj(times.split("to")[1].strip())
    contraints[name]["start_time"] = start_time
    contraints[name]["end_time"] = end_time
    contraints[name]["meeting_time"] = meeting_time
  return contraints


def validator_from_text(
    plan: list[str],
    processed_constraints: dict[str, Any],
    start_location: str,
    initial_time: str,
    dist_matrix: dict[str, Any],
):
  """Compute the number of valid meetings scheduled in the plan (text format)."""

  # This function is used when the generated plan follows the few-shot format.

  # Example:
  # You start at Russian Hill at 9:00AM.
  # You travel to Marina District in 7 minutes and arrive at 9:07AM.
  # You wait until 3:45PM.
  # You meet James for 75 minutes from 3:45PM to 5:00PM.

  met_with = {}

  score = 0
  cur_location = start_location
  cur_time = convert_to_time_obj(initial_time)
  for step in plan:
    try:
      if step.startswith("You start"):
        continue
      elif step.startswith("You travel"):
        destination = step.split("travel to ")[1].split(" in")[0].strip()
        cur_time = cur_time + datetime.timedelta(
            minutes=dist_matrix[cur_location][destination]
        )

        cur_location = destination
      elif step.startswith("You wait"):

        raw_end_time = step.split("wait until ")[1].split(".")[0].strip()
        end_time = convert_to_time_obj(raw_end_time)

        if end_time <= cur_time:
          raise ValueError("Cannot go backwards in time")

        cur_time = end_time
      elif step.startswith("You meet"):

        person = step.split("meet ")[1].split(" for")[0].strip()
        if person in met_with:
          raise ValueError(
              "Person {person} already met with {met_with}".format(
                  person=person, met_with=met_with[person]
              )
          )

        met_with[person] = 1
        new_time = cur_time + datetime.timedelta(
            minutes=processed_constraints[person]["meeting_time"]
        )

        if (
            cur_location == processed_constraints[person]["location"]
            and cur_time >= processed_constraints[person]["start_time"]
            and new_time <= processed_constraints[person]["end_time"]
        ):

          score += 1
          cur_time = new_time
        else:
          raise ValueError("Invalid meeting time or location")
      else:
        raise ValueError("Unknown plan format")

    except ValueError as e:
      print("Had error: {e} with step: {step}".format(e=e, step=step))
      break

  return score


def parse_text_plan(plan: str):
  """Parse the text plan into a list of steps."""

  prefix = "SOLUTION:"
  if prefix in plan:
    plan = plan[plan.find(prefix) + len(prefix):].strip()
  plan = plan.split(".")
  plan = [step.strip() for step in plan]
  final_plan = []
  for step in plan:
    if step:
      final_plan.append(step)
  return final_plan


# calendar_scheduling functions from evaluate_calendar_scheduling.py

def hour_to_num(hr_str):
  return float(hr_str.split(':')[0]) + (
      0.5 if hr_str.split(':')[1] == '30' else 0.0
  )


def _parse_response(response: str):
  """Parse the response.

  Returns a parsed suggested meeting time in (day, start_hour, end_hour).

  Args:
    response: Raw response from the model.

  Returns:
    A tuple of (day, start_hour, end_hour).
  """
  time_strs = re.findall(r'[A-Za-z]+, [0-9]+:[0-9]+ - [0-9]+:[0-9]+', response)
  if not time_strs:
    return '', -1, -1
  # If multiple matches are found, return the first one.
  time_str = time_strs[0]
  day, hour_str = (
      time_str.split(',')[0].strip(),
      time_str.split(',')[1].strip(),
  )
  start_hour, end_hour = (
      hour_str.split('-')[0].strip(),
      hour_str.split('-')[1].strip(),
  )
  return day, hour_to_num(start_hour), hour_to_num(end_hour)


def compute_solve_rate(responses: list[str], solutions: list[str]):
  """Computes solve rate by comparing model responses to golden solutions.

  Args:
    responses: A list of model responses.
    solutions: The corresponding list of golden solutions for the same tasks.

  Returns:
    A scalr solve rate.
  """
  solved_count = 0

  for r, s in zip(responses, solutions):
    r_day, r_start_hour, r_end_hour = _parse_response(r)
    s_day, s_start_hour, s_end_hour = _parse_response(s)
    if (
        r_day == s_day
        and r_start_hour == s_start_hour
        and r_end_hour == s_end_hour
    ):
      solved_count += 1
  return float(solved_count) / len(responses)
