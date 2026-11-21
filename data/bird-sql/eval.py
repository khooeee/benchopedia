"""Score BIRD-SQL queries by result-set equality on the pinned development DBs.

Prompt and execution-accuracy semantics follow the authors' baseline:
https://github.com/AlibabaResearch/DAMO-ConvAI/tree/7635e3f7fd7136cddc462d7f184fd497d5bd5e4c/bird/llm/src
"""

from contextlib import closing
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
from uuid import uuid4


ATTEMPTS = 1
TIMEOUT = 30
IMAGE = "python@sha256:a02e9c5406c416c504d6c9a1a306ff4080c3173f1008d192f953bd20382a2d5c"
DATABASE_SHA256 = {
    "california_schools": "c0903eec662e63068fd1d14403d3d6c1d473287fc10c4356333ea58f878db983",
    "card_games": "c98bdb57fe7474da798b407785544b9af0daaad5d61fd21e2a73309493bc1227",
    "codebase_community": "92101be6d2a9f6adceea59d38f6d1c556087f9eea1432432a21268cb1348036d",
    "debit_card_specializing": "b3d149ad05746dbbe5116e229e17e18f09c39db43cf117d9ef3441753608b691",
    "european_football_2": "f72f5c9b990371417288a67b27a02e601ef904d45525c2c9f7931fb01001c536",
    "financial": "d15d89cdb068a202b6f2b99342af44dffc1d52545b39ceaf62efdc0ba570101e",
    "formula_1": "79770caf966707e35516fa566e24b40ae515c74ec1ec4631235245645b87b24d",
    "student_club": "eb89bcfe97eefa386a27904ec5aa15159811a7eac894ec659a36e48fa9f76b77",
    "superhero": "75e94a2c3236ee3bb2c01fb97a1c4b4c1c269bcefd4eab1d04be323d2d0825b1",
    "thrombosis_prediction": "87583183c3dc472fba04de702965560a9d7c0a548836613f242317e0eeb83f00",
    "toxicology": "35ef27ae6bdfda530e125ed369666ac0abb8bc8c0bcc0ad09407f547ecb61a93",
}
SQL_FENCE = re.compile(r"```(?:sql|sqlite)?[ \t]*\n(.*?)\n```", re.S | re.I)
STOP = re.compile(r"--|\r?\n\r?\n|;|#")
ANSWER_START = re.compile(r"(?i)^(?:select|with)\b")
ROW_MEMORY_LIMIT = 128 * 1024 * 1024
ALLOWED_OPERATIONS = {sqlite3.SQLITE_READ, sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION,
                      sqlite3.SQLITE_RECURSIVE}


def data_dir():
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    return root / "build" / "bird-databases"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def databases_ready():
    root = data_dir()
    paths = ((root / (name + ".sqlite"), digest) for name, digest in DATABASE_SHA256.items())
    return all(path.is_file() and sha256(path) == digest for path, digest in paths)


@lru_cache(maxsize=1)
def check_setup():
    if not databases_ready():
        return "Run python3 data/bird-sql/setup_eval.py to install the pinned development databases"
    try:
        result = subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True, timeout=10)
        if result.returncode == 0:
            return None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "Start Docker and run python3 data/bird-sql/setup_eval.py to install the pinned SQLite runtime"


def fields(task):
    question, separator, trailing = task["prompt"].partition("\n\nDatabase: ")
    if not separator:
        raise ValueError(f"{task['key']}: missing database")
    database, _, evidence = trailing.partition("\n\nEvidence: ")
    if database not in DATABASE_SHA256:
        raise ValueError(f"{task['key']}: unexpected database")
    return question, database, evidence


def read_only(database, root=None):
    path = (data_dir() if root is None else root) / (database + ".sqlite")
    return sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)


@lru_cache(maxsize=None)
def schema(database):
    with closing(read_only(database)) as connection:
        return "\n\n".join(sql for (sql,) in connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table'"))


def messages(task):
    question, database, evidence = fields(task)
    text = (schema(database) + "\n\n"
            + f"-- External Knowledge: {evidence}\n"
            + "-- Using valid SQLite and understading External Knowledge, answer the following questions for the tables provided above.\n"
            + f"-- {question}\nGenerate the SQL after thinking step by step: \nSELECT ")
    return [{"role": "user", "content": text}]


def grade(task, output):
    reply = output.strip()
    matched = SQL_FENCE.fullmatch(reply)
    query = matched[1].strip() if matched else reply
    if not ANSWER_START.match(query):
        query = STOP.split(query, maxsplit=1)[0].strip()
    if not query:
        return "unparseable", None
    if not ANSWER_START.match(query):
        query = "SELECT " + query
    _, database, _ = fields(task)
    database_file = database + ".sqlite"
    name = f"benchopedia-bird-{uuid4().hex}"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--init", "--name", name, "--pull=never",
             "--log-driver", "none", "--network", "none", "--read-only", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges", "--user", "65534:65534",
             "--memory", "2g", "--memory-swap", "2g", "--pids-limit", "32",
             "--tmpfs", "/tmp:size=1g,mode=1777,nosuid,nodev,noexec",
             "--mount", f"type=bind,src={Path(__file__).resolve()},dst=/grader.py,readonly",
             "--mount", f"type=bind,src={data_dir() / database_file},dst=/databases/{database_file},readonly",
             "-i", IMAGE, "python", "-I", "/grader.py", database],
            input=json.dumps({"prediction": query, "gold": task["solution"]}), text=True,
            capture_output=True, timeout=TIMEOUT + 10,
        )
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        return "fail", query
    if result.returncode or result.stdout.strip() not in ("0", "1"):
        raise RuntimeError(f"{task['key']}: SQL grader worker failed ({result.stderr.strip()})")
    return ("pass" if result.stdout.strip() == "1" else "fail"), query


def authorize(operation, first, second, db_name, origin):
    if operation == sqlite3.SQLITE_FUNCTION and second.lower() == "load_extension":
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK if operation in ALLOWED_OPERATIONS else sqlite3.SQLITE_DENY


def query_rows(connection, sql):
    unique = set()
    used = 0
    for row in connection.execute(sql):
        if row not in unique:
            used += sys.getsizeof(row) + sum(map(sys.getsizeof, row)) + 64
            if used > ROW_MEMORY_LIMIT:
                raise MemoryError("SQL result set exceeds the worker memory budget")
            unique.add(row)
    return unique


def compare(database, queries, root):
    deadline = time.monotonic() + TIMEOUT
    with closing(read_only(database, root)) as connection:
        connection.execute("PRAGMA hard_heap_limit=268435456")
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA temp_store=FILE")
        if database == "european_football_2":
            # The persistent player_api_id index avoids a scan of Player for each match.
            connection.execute("PRAGMA automatic_index=OFF")
        connection.set_authorizer(authorize)
        connection.set_progress_handler(lambda: time.monotonic() >= deadline, 10_000)
        try:
            predicted = query_rows(connection, queries["prediction"])
            expected = query_rows(connection, queries["gold"])
        except (sqlite3.Error, MemoryError):
            return False
    return predicted == expected


if __name__ == "__main__":
    print(int(compare(sys.argv[1], json.load(sys.stdin), Path("/databases"))))
