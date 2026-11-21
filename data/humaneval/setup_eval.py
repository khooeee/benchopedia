"""Install the pinned Python image used to check HumanEval completions."""

import subprocess

from eval import IMAGE


if __name__ == "__main__":
    subprocess.run(["docker", "pull", IMAGE], check=True)
