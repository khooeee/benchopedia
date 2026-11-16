"""Load optional, reviewed score snapshots without network access."""

import json
import math
import sqlite3
from urllib.parse import urlsplit


def _finite_number(value):
    if type(value) not in (int, float):
        raise ValueError("expected a finite JSON number")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError("expected a finite JSON number") from error
    if not math.isfinite(number):
        raise ValueError("expected a finite JSON number")
    return number


def _finite_float(value):
    return _finite_number(float(value))


def _reject_constant(value):
    raise ValueError(f"non-standard JSON constant: {value}")


def _insert(db, table, row):
    columns_info = {column[1]: column[2] for column in db.execute(f"PRAGMA table_info({table})")}
    unknown = row.keys() - columns_info.keys()
    if unknown:
        raise ValueError(f"unknown {table} fields: {', '.join(sorted(unknown))}")
    for column, value in row.items():
        if columns_info[column] == "TEXT" and value is not None and not isinstance(value, str):
            raise ValueError(f"{column} must be a JSON string or null")
    columns = ', '.join(f'"{column}"' for column in row)
    placeholders = ', '.join('?' for _ in row)
    db.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(row.values()))


def _prepare(db, table, row, benchmark_id):
    row = dict(row)
    if table == "benchmark_metric":
        if "benchmark_id" in row:
            raise ValueError("benchmark_id is supplied by the containing directory")
        row["benchmark_id"] = benchmark_id
        if type(row.get("higher_is_better")) is not bool:
            raise ValueError("higher_is_better must be a JSON boolean")
        for key in ("min_value", "max_value"):
            if row.get(key) is not None:
                row[key] = _finite_number(row[key])
    elif table == "evaluation_setup":
        metric = db.execute("SELECT benchmark_id FROM benchmark_metric WHERE id = ?",
                            (row.get("metric_id"),)).fetchone()
        if not metric or metric[0] != benchmark_id:
            raise ValueError("metric_id must belong to this benchmark")
        if not isinstance(row.get("configuration"), dict):
            raise ValueError("configuration must be a JSON object")
        row["configuration"] = json.dumps(row["configuration"], ensure_ascii=False,
                                          allow_nan=False, sort_keys=True)
    else:
        setup = db.execute("""SELECT m.benchmark_id FROM evaluation_setup e
                            JOIN benchmark_metric m ON m.id = e.metric_id WHERE e.id = ?""",
                           (row.get("setup_id"),)).fetchone()
        if not setup or setup[0] != benchmark_id:
            raise ValueError("setup_id must belong to this benchmark")
        row["value"] = _finite_number(row.get("value"))
    for key in ("documentation_url", "source_url"):
        if key in row:
            url = urlsplit(row[key]) if isinstance(row[key], str) else None
            if not url or url.scheme != "https" or not url.hostname or any(
                    char.isspace() for char in row[key]):
                raise ValueError(f"{key} must be an absolute HTTPS URL without whitespace")
    return row


def load_scores(db, path, benchmark_id, errors):
    """Load metrics, setups and scores in dependency order, collecting errors."""
    if not path.exists():
        return
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"),
                              parse_constant=_reject_constant, parse_float=_finite_float)
        groups = {"metrics": "benchmark_metric", "setups": "evaluation_setup", "scores": "score"}
        if not isinstance(snapshot, dict) or snapshot.keys() != groups.keys():
            raise ValueError("expected an object with metrics, setups and scores arrays")
        for key in groups:
            if not isinstance(snapshot[key], list):
                raise ValueError(f"{key} must be an array")
    except (ValueError, OSError) as error:
        errors.append(f"{path}: {error}")
        return
    for key, table in groups.items():
        for index, record in enumerate(snapshot[key], start=1):
            try:
                if not isinstance(record, dict):
                    raise ValueError("expected a JSON object")
                row = _prepare(db, table, record, benchmark_id)
                _insert(db, table, row)
            except (ValueError, TypeError, OverflowError, sqlite3.Error) as error:
                errors.append(f"{path}:{key}[{index}]: {error}")
