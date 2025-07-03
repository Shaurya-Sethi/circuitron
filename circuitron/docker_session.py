from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class DockerSession:
    """Manage a persistent Docker container for running commands."""

    image: str
    container_name: str
    started: bool = False

    def _run(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, capture_output=True, text=True, **kwargs)

    def start(self) -> None:
        """Start the container if it isn't already running."""
        if self.started:
            return
        ps_cmd = [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"name={self.container_name}",
            "--format",
            "{{.Status}}",
        ]
        try:
            proc = self._run(ps_cmd, check=True)
        except subprocess.CalledProcessError as exc:  # pragma: no cover - docker error
            logging.error(
                "Failed to check for existing container %s: %s",
                self.container_name,
                exc.stderr.strip(),
            )
            raise

        if proc.stdout.strip():
            status = proc.stdout.strip().lower()
            if status.startswith("up"):
                self.started = True
                return
            self._run(["docker", "rm", "-f", self.container_name], check=True)

        cmd = [
            "docker",
            "run",
            "-d",
            "--network",
            "none",
            "--memory",
            "512m",
            "--pids-limit",
            "256",
            "--name",
            self.container_name,
            self.image,
            "sleep",
            "infinity",
        ]
        try:
            self._run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            logging.error(
                "Failed to start container %s: %s",
                self.container_name,
                exc.stderr.strip(),
            )
            raise RuntimeError(
                "Failed to start Docker container. Ensure Docker is installed and that the current user has permission to run containers."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            logging.error(
                "Failed to start container %s: %s",
                self.container_name,
                str(exc).strip(),
            )
            raise
        self.started = True

    def exec_python(self, script: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        """Execute a Python script inside the running container."""
        self.start()
        cmd = ["docker", "exec", "-i", self.container_name, "python", "-c", script]
        return self._run(cmd, timeout=timeout, check=True)

    def exec_erc(self, script_path: str, wrapper: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
        """Copy a script and run ERC inside the container."""
        self.start()
        cp_cmd = ["docker", "cp", script_path, f"{self.container_name}:/tmp/script.py"]
        self._run(cp_cmd, check=True)
        cmd = ["docker", "exec", "-i", self.container_name, "python", "-c", wrapper]
        return self._run(cmd, timeout=timeout, check=True)

    def stop(self) -> None:
        """Stop and remove the container."""
        if not self.started:
            return
        subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
        self.started = False
