#!/usr/bin/env python3
"""Run the test suite against a specific openai-agents version.

Creates a temporary virtual environment, installs dependencies with the
requested ``openai-agents`` version, installs the project in editable
mode without its dependencies, and finally runs ``pytest -q``.
"""
import argparse
import subprocess
import tempfile
import venv
from pathlib import Path


def run(version: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        venv.create(tmp, with_pip=True)
        py = Path(tmp) / "bin" / "python"
        # Prepare requirements with the desired agents version
        req_text = Path("requirements.txt").read_text().splitlines()
        req_lines = [
            (f"openai-agents=={version}" if line.startswith("openai-agents") else line)
            for line in req_text
            if line and not line.startswith("#")
        ]
        req_file = Path(tmp) / "reqs.txt"
        req_file.write_text("\n".join(req_lines))
        subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(req_file)])
        subprocess.check_call([str(py), "-m", "pip", "install", "pytest"])
        subprocess.check_call([str(py), "-m", "pip", "install", "-e", ".", "--no-deps"])
        return subprocess.call([str(py), "-m", "pytest", "-q"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="openai-agents version to test against")
    args = parser.parse_args()
    raise SystemExit(run(args.version))


if __name__ == "__main__":
    main()
