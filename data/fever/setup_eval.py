"""Index the titles and evidence sentences in FEVER's pinned Wikipedia snapshot."""

import argparse
from contextlib import closing
from pathlib import Path
import hashlib
import importlib
import json
import shutil
import sqlite3
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile


SOURCE = importlib.import_module("import")
DESTINATION = SOURCE.BENCHMARK_DIR.parents[1] / "build" / "fever-wikipedia.sqlite"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def feed(archive, conn):
    with ZipFile(archive) as pages:
        names = sorted(name for name in pages.namelist() if SOURCE.WIKI_MEMBER.fullmatch(name))
        if not names:
            raise ValueError("The pinned archive contains no page files")
        for number, name in enumerate(names, 1):
            batch = []
            with pages.open(name) as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    page = json.loads(line)
                    text = "\n".join(item.partition("\t")[0] + "\t" + item.split("\t", 2)[1]
                                      for item in page["lines"].split("\n") if "\t" in item)
                    if text:
                        batch.append((page["id"], text))
            conn.executemany("INSERT INTO pages(id, lines) VALUES (?, ?)", batch)
            conn.commit()
            print(f"Indexed source file {number} of {len(names)}", flush=True)
        query = "INSERT INTO titles(rowid, title) SELECT rowid, replace(id, '_', ' ') FROM pages"
        conn.execute(query)
        conn.execute("INSERT INTO metadata VALUES (?)", (SOURCE.WIKI_SHA256,))
        conn.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="use a local copy of the pinned zip")
    args = parser.parse_args()
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=DESTINATION.parent) as temporary:
        temp = Path(temporary)
        archive = args.archive
        if archive is None:
            archive = temp / "wiki-pages.zip"
            with urlopen(SOURCE.WIKI_URL, timeout=120) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
        if sha256(archive) != SOURCE.WIKI_SHA256:
            raise SystemExit("FEVER Wikipedia archive checksum differs from the pinned release")
        db = temp / DESTINATION.name
        with closing(sqlite3.connect(db)) as conn:
            conn.executescript("""
                PRAGMA journal_mode=OFF;
                PRAGMA synchronous=OFF;
                CREATE TABLE pages (id TEXT NOT NULL, lines TEXT NOT NULL);
                CREATE VIRTUAL TABLE titles USING fts5(title);
                CREATE TABLE metadata (wiki_sha256 TEXT PRIMARY KEY);
            """)
            feed(archive, conn)
        db.replace(DESTINATION)
    print(f"Built {DESTINATION}")


if __name__ == "__main__":
    main()
