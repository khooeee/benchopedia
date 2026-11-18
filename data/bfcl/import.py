"""Import all 4,733 BFCL v4 test entries from a pinned commit of the Gorilla repository.

Run from the repository root: python3 data/bfcl/import.py
Only Python's standard library is required. Imported data is never executed.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "ShishirPatil/gorilla"
DATA = "berkeley-function-call-leaderboard/bfcl_eval/data"
# Scored test category and its documented entry count, in leaderboard order.
CATEGORIES = {
    "simple_python": 400,
    "simple_java": 100,
    "simple_javascript": 50,
    "multiple": 200,
    "parallel": 200,
    "parallel_multiple": 200,
    "irrelevance": 240,
    "live_simple": 258,
    "live_multiple": 1053,
    "live_parallel": 16,
    "live_parallel_multiple": 24,
    "live_irrelevance": 884,
    "live_relevance": 16,
    "multi_turn_base": 200,
    "multi_turn_miss_func": 200,
    "multi_turn_miss_param": 200,
    "multi_turn_long_context": 200,
    "web_search": 100,
    "memory": 155,
}
# The expected output of these categories is no function call, so they have no answer file.
WITHOUT_ANSWERS = {"irrelevance", "live_irrelevance", "live_relevance"}
# Memory scenario and the number of conversations that fill memory before its questions.
MEMORY_SCENARIOS = {"customer": 10, "finance": 7, "healthcare": 5, "notetaker": 5, "student": 10}
EXPECTED_COUNT = sum(CATEGORIES.values()) + sum(MEMORY_SCENARIOS.values())
# Tool documentation the harness supplies for multi-turn and agentic entries.
FUNCTION_DOCS = {
    "GorillaFileSystem": ["gorilla_file_system.json"],
    "MathAPI": ["math_api.json"],
    "MessageAPI": ["message_api.json"],
    "TwitterAPI": ["posting_api.json"],
    "TicketAPI": ["ticket_api.json"],
    "TradingBot": ["trading_bot.json"],
    "TravelAPI": ["travel_booking.json"],
    "VehicleControlAPI": ["vehicle_control.json"],
    "WebSearchAPI": ["web_search.json"],
    # A memory entry is scored once per backend, each with its own tools.
    "MemoryAPI": ["memory_kv.json", "memory_rec_sum.json", "memory_vector.json"],
}
ENTRY_FIELDS = {"id", "question", "function", "involved_classes", "initial_config", "path",
                "missed_function", "excluded_function", "scenario", "topic"}
ANSWER_FIELDS = {"id", "ground_truth", "source", "num_hops"}


def fetch(revision, path):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{path}"
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read().decode("utf-8")


def records(revision, path):
    """Yield each line of an upstream JSON Lines file with its line number."""
    for number, line in enumerate(fetch(revision, path).split("\n"), start=1):
        if line.strip():
            yield number, json.loads(line)


def blob(revision, path, line):
    return f"https://github.com/{REPOSITORY}/blob/{revision}/{path}#L{line}"


def fenced(where, language, text):
    if "~~~" in text:
        raise ValueError(f"{where}: content cannot be fenced intact")
    return f"~~~{language}\n{text}\n~~~"


def as_json(where, value):
    return fenced(where, "json", json.dumps(value, indent=2, ensure_ascii=False))


def turn_sections(where, question):
    """Render the conversation the model is given, one section per message."""
    sections = []
    for index, turn in enumerate(question, start=1):
        if not turn:
            # The miss_func category leaves a turn empty: the harness supplies the
            # held-out functions there instead of a user message.
            sections.append(f"# Turn {index} · no message")
            continue
        for message in turn:
            sections.append(f"# Turn {index} · {message['role']}")
            sections.append(fenced(where, "text", message["content"]))
    return sections


def function_sections(where, entry, docs):
    """Render the tools the model may call, from the entry or the predefined backends."""
    if "function" in entry:
        return ["# Available functions", as_json(where, entry["function"])]
    sections = []
    for name in entry["involved_classes"]:
        for doc in FUNCTION_DOCS[name]:
            label = doc[: -len(".json")]
            sections.append(f"# Available functions · {label}")
            sections.append(as_json(where, docs[doc]))
    return sections


def environment_url(revision, entry):
    """Link the tool documentation behind an entry, or the directory when it uses several."""
    if "function" in entry:
        return None
    docs = [doc for name in entry["involved_classes"] for doc in FUNCTION_DOCS[name]]
    folder = f"{DATA}/multi_turn_func_doc"
    if len(docs) == 1:
        return f"https://github.com/{REPOSITORY}/blob/{revision}/{folder}/{docs[0]}"
    return f"https://github.com/{REPOSITORY}/tree/{revision}/{folder}"


def to_task(revision, category, entry, line, path, answers, docs):
    where = entry["id"]
    unknown = set(entry) - ENTRY_FIELDS
    if unknown:
        raise ValueError(f"{where}: unsupported fields {sorted(unknown)}")
    sections = [f"{where} ({category})"]
    sections += turn_sections(where, entry["question"])
    sections += function_sections(where, entry, docs)
    if "initial_config" in entry:
        sections.append("# Initial state of the backend systems")
        sections.append(as_json(where, entry["initial_config"]))
    if "missed_function" in entry:
        sections.append("# Functions held out until the model asks for them, by turn")
        sections.append(as_json(where, entry["missed_function"]))
    if "scenario" in entry:
        sections.append("# Memory scenario")
        sections.append(entry["scenario"])
    if "topic" in entry:
        sections.append("# Conversation topic")
        sections.append(entry["topic"])
    task = {"key": where, "prompt": "\n\n".join(sections),
            "prompt_source_url": blob(revision, path, line)}
    answer = answers.get(where)
    if answer is not None:
        record, answer_line, answer_path = answer
        unknown = set(record) - ANSWER_FIELDS
        if unknown:
            raise ValueError(f"{where}: unsupported answer fields {sorted(unknown)}")
        rest = {field: value for field, value in record.items() if field != "id"}
        value = rest["ground_truth"] if set(rest) == {"ground_truth"} else rest
        task["solution"] = json.dumps(value, indent=2, ensure_ascii=False)
        task["solution_source_url"] = blob(revision, answer_path, answer_line)
    environment = environment_url(revision, entry)
    if environment is not None:
        task["environment_url"] = environment
    return task


def load_answers(revision, category):
    path = f"{DATA}/possible_answer/BFCL_v4_{category}.json"
    return {record["id"]: (record, line, path) for line, record in records(revision, path)}


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit(f"The declared scope must be all {EXPECTED_COUNT} BFCL v4 test entries.")
    # Each tool documentation file holds one function per line, like the entry files.
    docs = {doc: [entry for _, entry in records(revision, f"{DATA}/multi_turn_func_doc/{doc}")]
            for docs_for_class in FUNCTION_DOCS.values() for doc in docs_for_class}
    sources = [(category, f"{DATA}/BFCL_v4_{category}.json", count)
               for category, count in CATEGORIES.items()]
    sources += [("memory", f"{DATA}/memory_prereq_conversation/memory_{scenario}.json", count)
                for scenario, count in MEMORY_SCENARIOS.items()]
    tasks = []
    for category, path, count in sources:
        answers = {} if category in WITHOUT_ANSWERS else load_answers(revision, category)
        found = 0
        for line, entry in records(revision, path):
            tasks.append(to_task(revision, category, entry, line, path, answers, docs))
            found += 1
        if found != count:
            sys.exit(f"{path}: expected {count} entries, found {found}.")
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("BFCL entry IDs are not unique.")
    solved = sum("solution" in task for task in tasks)
    if solved != 3556:
        sys.exit(f"Expected 3,556 entries with a reference answer, found {solved}.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} BFCL v4 entries ({solved:,} with reference answers) to {out}")


if __name__ == "__main__":
    main()
