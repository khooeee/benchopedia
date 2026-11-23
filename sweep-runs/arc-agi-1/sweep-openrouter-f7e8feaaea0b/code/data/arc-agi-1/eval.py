"""ARC-AGI-1 inference and per-task accuracy using the pinned ARC Prize harness.

The prompt template and response parser come from the MIT-licensed harness.
https://github.com/arcprize/arc-agi-benchmarking/blob/a4e7c997a2015a3209d4bc7c778aab18faef1cdb/src/arc_agi_benchmarking/prompts/system_prompt.txt
https://github.com/arcprize/arc-agi-benchmarking/blob/a4e7c997a2015a3209d4bc7c778aab18faef1cdb/src/arc_agi_benchmarking/utils/parsing.py
https://github.com/arcprize/arc-agi-benchmarking/blob/a4e7c997a2015a3209d4bc7c778aab18faef1cdb/main.py
See LICENSE-grader for the ARC Prize Foundation copyright and license.
"""

import json
import re
from typing import List, Optional


ATTEMPTS = 1
PREDICTIONS_PER_INPUT = 2
CALLS_PER_PREDICTION = 2
PROMPT = 'You are participating in a puzzle solving competition. You are an expert at solving puzzles.\n\nBelow is a list of input and output pairs with a pattern. Your goal is to identify the pattern or transformation in the training examples that maps the input to the output, then apply that pattern to the test input to give a final output.\n\nRespond in the format of the training output examples\n\n--Training Examples--\n{training_examples}\n--End of Training Examples--\n\n--Test Input--\n{test_input}\n--End of Test Input--\n\nYour response:'
GRID_BLOCK = re.compile(r"\n~~~\n([0-9\n]+)\n~~~")
TEST_SECTION = "\n\n## Test input "


def backscan_json_parser(log_str: str) -> Optional[List[List[int]]]:
    """
    Extract the last valid JSON substring that matches the List[List] structure
    from the given log string by scanning backwards from the end.

    Parameters:
        log_str (str): The full log output text.

    Returns:
        The parsed List[List] object if found and valid, otherwise None.
    """
    last_bracket_idx = -1
    closing_bracket = None
    for i in range(len(log_str) - 1, -1, -1):
        char = log_str[i]
        if char in (']', '}'):
            last_bracket_idx = i
            closing_bracket = char
            break

    if last_bracket_idx == -1:
        return None

    opening_bracket = '[' if closing_bracket == ']' else '{'

    bracket_counter = 1 # Start at 1 to account for the found closing bracket
    start_idx = -1

    for i in range(last_bracket_idx - 1, -1, -1):
        char = log_str[i]
        if char == closing_bracket:
            bracket_counter += 1
        elif char == opening_bracket:
            bracket_counter -= 1
            if bracket_counter == 0:
                start_idx = i
                break

    if start_idx == -1:
        return None

    json_candidate = log_str[start_idx:last_bracket_idx+1]

    try:
        parsed_json = json.loads(json_candidate)

        # Validate the structure: must be a non-empty list of lists.
        if isinstance(parsed_json, list) and parsed_json and all(isinstance(row, list) for row in parsed_json):
            return parsed_json
        else:
            return None

    except json.JSONDecodeError:
        return None

def extract_from_boxed(log_str: str) -> Optional[List[List[int]]]:
    """
    Extracts JSON from a LaTeX-style \\boxed{} command in a string.
    """
    match = re.search(r"\\boxed\{(.*?)\}", log_str, re.DOTALL)
    if match:
        content = match.group(1).strip()
        try:
            # The content inside boxed is often a list of lists
            parsed_json = json.loads(content)
            if isinstance(parsed_json, list) and all(isinstance(i, list) for i in parsed_json):
                return parsed_json
        except json.JSONDecodeError:
            # If json.loads fails, it's not the JSON we're looking for.
            pass
    return None


# --- Main Parsing Orchestrator ---

def parse_and_validate_json(response: str) -> Optional[List[List[int]]]:
    """
    Orchestrates parsing by trying the provider extractor.
    Returns the parsed List[List[int]] or raises ValueError if validation fails.
    """
    parsing_attempts = [
        extract_from_boxed,
        backscan_json_parser
    ]

    for parser in parsing_attempts:
        result = parser(response)
        if result is not None:
            # Validate the structure: must be list of lists
            if isinstance(result, list) and all(isinstance(row, list) for row in result):
                return result # Return immediately on first success and validation
            else:
                # Raise error if structure is invalid, triggering retry in main loop
                raise ValueError(f"Parser {parser.__name__} produced invalid structure: {result!r}")

    # Raise an error here if no method works, triggering retry in main loop
    raise ValueError(f"Failed to parse response after all attempts: {response!r}")


def grid(rows):
    return [[int(cell) for cell in line] for line in rows.split("\n")]


def guesses(outputs):
    """Recover prediction slots from each response and any retry."""
    predictions = []
    calls = 0
    for output in outputs:
        calls += 1
        try:
            prediction = parse_and_validate_json(output)
        except ValueError:
            prediction = None
        if prediction is not None or calls == CALLS_PER_PREDICTION:
            predictions.append(prediction)
            calls = 0
    return predictions


def next_messages(task, outputs):
    demonstrations, separator, tests = task["prompt"].partition(TEST_SECTION)
    if not separator:
        raise ValueError(f"{task['key']}: missing test inputs")
    test_inputs = GRID_BLOCK.findall(tests)
    index = len(guesses(outputs)) // PREDICTIONS_PER_INPUT
    if index >= len(test_inputs):
        return None

    examples = GRID_BLOCK.findall(demonstrations)
    if not examples or len(examples) % 2:
        raise ValueError(f"{task['key']}: expected paired demonstration grids")
    training = "".join(
        f"--Example {number}-- \n\n INPUT: \n\n{json.dumps(grid(before))}\n\n"
        f"OUTPUT: \n\n{json.dumps(grid(after))}\n\n"
        for number, (before, after) in enumerate(zip(examples[::2], examples[1::2]))
    )
    prompt = PROMPT.format(training_examples=training, test_input=json.dumps(grid(test_inputs[index])))
    return [{"role": "user", "content": prompt}]


def answers(task):
    return [grid(part.split("\n", 1)[1]) for part in task["solution"].split("\n\n")]


def score_responses(task, outputs):
    targets = answers(task)
    predictions = guesses(outputs)
    if len(predictions) != len(targets) * PREDICTIONS_PER_INPUT:
        raise ValueError(f"{task['key']}: incomplete ARC predictions")
    solved = sum(
        target in predictions[index:index + PREDICTIONS_PER_INPUT]
        for index, target in zip(range(0, len(predictions), PREDICTIONS_PER_INPUT), targets)
    )
    return {"accuracy": solved / len(targets)}


def reference_responses(task):
    return [json.dumps(target) for target in answers(task) for _ in range(PREDICTIONS_PER_INPUT)]
