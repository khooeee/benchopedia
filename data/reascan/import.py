"""Import the two complete ReaSCAN v1.1 syntax test sets."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryFile
from urllib.request import Request, urlopen
from zipfile import ZipFile


HERE = Path(__file__).resolve().parent
DOWNLOAD = (
    "https://drive.usercontent.google.com/download"
    "?id=1foVr1MPqPqBQgoOqVgVFWUIwXERPMM4I&export=download&confirm=t"
)
ARCHIVE_SIZE = 1382196302
CENTRAL_DIRECTORY = (1381628594, ARCHIVE_SIZE - 1)
SPLITS = {
    "c1": (8375, (1094339, 3823871)),
    "c2": (8003, (998593196, 1000996045)),
}
DIRECTIONS = ("east", "south", "west", "north")
ACTIONS = {"walk", "push", "pull", "turn left", "turn right", "stay"}


def download_ranges(target):
    # Populate a sparse ZIP with the central directory and the two selected
    # members so the full 1.38 GB upstream release need not be fetched.
    for start, end in [CENTRAL_DIRECTORY, *(limits for _, limits in SPLITS.values())]:
        request = Request(DOWNLOAD, headers={"Range": f"bytes={start}-{end}"})
        with urlopen(request, timeout=90) as response:
            content_range = f"bytes {start}-{end}/{ARCHIVE_SIZE}"
            if response.status != 206 or response.headers.get("Content-Range") != content_range:
                raise ValueError(f"The upstream server did not return the requested range {content_range}")
            size = end - start + 1
            payload = response.read(size + 1)
        if len(payload) != size:
            raise ValueError(f"Incomplete ReaSCAN archive range {start}-{end}")
        target.seek(start)
        target.write(payload)
    target.flush()


def position(record, grid_size):
    row, column = (int(record[axis]) for axis in ("row", "column"))
    if not (0 <= row < grid_size and 0 <= column < grid_size):
        raise ValueError("ReaSCAN position is outside the grid")
    return row, column


def render_prompt(command, situation):
    grid_size = int(situation["grid_size"])
    row, column = position(situation["agent_position"], grid_size)
    facing = int(situation["agent_direction"])
    if grid_size != 6 or situation["carrying_object"] is not None or not 0 <= facing < len(DIRECTIONS):
        raise ValueError("Unexpected initial ReaSCAN grid or agent state")
    objects = []
    for placed in situation["placed_objects"].values():
        object_row, object_column = position(placed["position"], grid_size)
        attributes = placed["object"]
        objects.append((object_row, object_column, attributes["shape"], attributes["color"], int(attributes["size"])))
    lines = [
        "Command: " + " ".join(command.split(",")),
        f"Grid: {grid_size} rows and {grid_size} columns, numbered from 0.",
        f"Agent: row {row}, column {column}, facing {DIRECTIONS[facing]}.",
        "Objects (row, column):",
    ]
    return "\n\n".join(lines) + "\n" + "\n".join(
        f"- ({object_row}, {object_column}): size {size} {color} {shape}"
        for object_row, object_column, shape, color, size in sorted(objects)
    )


def load_tasks(archive, benchmark):
    tasks = []
    digest = sha256()
    for condition, (expected_count, _) in SPLITS.items():
        member = f"ReaSCAN-v1.1/ReaSCAN-compositional-{condition}/data-compositional-splits.txt"
        payload = archive.read(member)
        digest.update(payload)
        dataset = json.loads(payload)
        rows = dataset["examples"]["test"]
        if len(rows) != expected_count:
            raise ValueError(f"{condition} has {len(rows)} examples, expected {expected_count}")
        for number, row in enumerate(rows, 1):
            command, solution = row["command"], row["target_commands"]
            if not command or not set(solution.split(",")) <= ACTIONS:
                raise ValueError(f"Bad command or action sequence in {condition} row {number}")
            tasks.append({
                "key": f"reascan-{condition}-{number:04d}",
                "prompt": render_prompt(command, row["situation"]),
                "solution": solution,
                "prompt_source_url": benchmark["dataset_url"],
                "solution_source_url": benchmark["dataset_url"],
            })
    if benchmark["dataset_revision"] != "sha256:" + digest.hexdigest():
        raise ValueError("C1 and C2 archive members do not match the pinned SHA-256")
    return tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="read an existing ReaSCAN-v1.1.zip")
    args = parser.parse_args()
    benchmark = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    with (args.archive.open("rb") if args.archive else TemporaryFile()) as source:
        if args.archive is None:
            download_ranges(source)
        with ZipFile(source) as archive:
            tasks = load_tasks(archive, benchmark)
    if len(tasks) != benchmark["task_count"] or len({task["key"] for task in tasks}) != len(tasks):
        raise ValueError("ReaSCAN count or identifiers differ from the declared scope")

    with NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False
    ) as temporary:
        path = Path(temporary.name)
        try:
            for task in tasks:
                temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
            temporary.close()
            path.replace(HERE / "tasks.jsonl")
        finally:
            path.unlink(missing_ok=True)
    print(f"Imported {len(tasks):,} ReaSCAN C1 and C2 test examples.")


if __name__ == "__main__":
    main()
