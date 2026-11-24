"""Import the PrOntoQA-OOD rule-generalization conditions from Figure 11."""

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from zipfile import ZipFile


HERE = Path(__file__).resolve().parent
REPO = "asaparov/prontoqa"
ARCHIVE = "generated_ood_data.zip"
ARCHIVE_SHA256 = "0becba04e1e1eb80593709c6a3db2a46badd5587a29587ffaeb68ed5068c9de9"
SPLITS = {
    "and-elim": "2hop_OOD_AndElim_3proofwidth_random_noadj.json",
    "and-intro": "2hop_OOD_AndIntro_3proofwidth_random_noadj.json",
    "contradiction": "1hop_OOD_ProofByContra_random_noadj.json",
    "implication-elim": "2hop_OOD_ModusPonens_random_noadj.json",
    "or-elim": "1hop_OOD_OrElim_3proofwidth_random_noadj.json",
    "or-intro": "2hop_OOD_OrIntro_3proofwidth_random_noadj.json",
}
DEMONSTRATIONS = tuple(f"in_context_example{index}" for index in range(8))


def proof_record(record):
    premises, query, proof = (record[field] for field in ("question", "query", "chain_of_thought"))
    if (not isinstance(premises, str) or not premises.strip() or "\n" in premises
            or not isinstance(query, str) or not query.startswith("Prove: ") or "\n" in query
            or not isinstance(proof, list) or not proof
            or any(not isinstance(step, str) or not step.strip() for step in proof)):
        raise ValueError("Expected the released premise, query, and proof format")
    return f"Q: {premises} {query}", " ".join(proof)


def load_tasks(payload, revision):
    if sha256(payload).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("PrOntoQA-OOD archive does not match the pinned SHA-256")
    source = f"https://github.com/{REPO}/blob/{revision}/{ARCHIVE}"
    expected = {f"example{number}" for number in range(1, 101)}
    tasks = []
    with ZipFile(BytesIO(payload)) as archive:
        for rule, file in SPLITS.items():
            rows = json.loads(archive.read(file))
            if set(rows) != expected:
                raise ValueError(f"{file} does not contain the complete 100-example condition")
            for number in range(1, 101):
                records = rows[f"example{number}"]
                if set(records) != {*DEMONSTRATIONS, "test_example"}:
                    raise ValueError(f"{file} example{number} does not have eight demonstrations")
                question, reference = proof_record(records["test_example"])
                newline = "\n\n" if "\n\n" in reference else "\n"
                demonstrations = []
                for name in DEMONSTRATIONS:
                    example_question, example_proof = proof_record(records[name])
                    demonstrations.append(f"{example_question}{newline}A: {example_proof}")
                test = f"{question}{newline}A:"
                tasks.append({
                    "key": f"prontoqa-ood-{rule}-{number:03d}",
                    "prompt": (newline + "\n").join([*demonstrations, test]),
                    "solution": reference,
                    "prompt_source_url": source,
                    "solution_source_url": source,
                })
    return tasks


def main():
    benchmark = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must be an immutable Git commit")
    url = f"https://raw.githubusercontent.com/{REPO}/{revision}/{ARCHIVE}"
    with urlopen(url, timeout=90) as response:
        tasks = load_tasks(response.read(), revision)
    if len(tasks) != benchmark["task_count"] or len({task["key"] for task in tasks}) != len(tasks):
        raise ValueError("PrOntoQA-OOD count or identifiers differ from the declared scope")
    tasks.sort(key=lambda task: task["key"])

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
    print(f"Imported {len(tasks):,} PrOntoQA-OOD rule-generalization examples.")


if __name__ == "__main__":
    main()
