from __future__ import annotations

import logging
import subprocess
import atexit
import os
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List
import threading
from .utils import convert_windows_path_for_docker


def cleanup_stale_containers(prefix: str) -> None:
    """Remove stopped containers whose names start with ``prefix``."""
    ps_cmd = [
        "docker",
        "ps",
        "-a",
        "--filter",
        f"name={prefix}",
        "--format",
        "{{.Names}} {{.Status}}",
    ]
    try:
        proc = subprocess.run(ps_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:  # pragma: no cover - docker failure
        logging.error("Failed to list containers with prefix %s", prefix)
        return
    for line in proc.stdout.splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        name, status = parts
        if not status.lower().startswith("up"):
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)


@dataclass
class DockerSession:
    """Manage a persistent Docker container for running commands."""

    image: str
    container_name: str
    started: bool = False
    base_prefix: str = field(init=False)
    volumes: Dict[str, str] = field(default_factory=dict)
    _lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Initialize dynamic attributes and register cleanup."""
        if "-" in self.container_name:
            self.base_prefix = self.container_name.rsplit("-", 1)[0] + "-"
        else:
            self.base_prefix = self.container_name
        atexit.register(self.stop)

    def _run(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, capture_output=True, text=True, **kwargs)

    def _health_check(self) -> bool:
        """Return ``True`` if SKiDL imports successfully inside the container."""
        try:
            proc = self._run(
                [
                    "docker",
                    "exec",
                    self.container_name,
                    "python3",
                    "-c",
                    "import skidl",
                ],
                check=True,
            )
            return proc.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def start(self) -> None:
        """Ensure the container is running."""
        with self._lock:
            cleanup_stale_containers(self.base_prefix)
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

            running = False
            if proc.stdout.strip():
                status = proc.stdout.strip().lower()
                if status.startswith("up"):
                    running = True
                else:
                    self._run(["docker", "rm", "-f", self.container_name], check=True)

            if running:
                if self._health_check():
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
            ]
            for host, container in self.volumes.items():
                try:
                    cont_path = convert_windows_path_for_docker(container)
                except ValueError:
                    cont_path = container
                cmd.extend(["-v", f"{host}:{cont_path}"])
            cmd += [
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

    def exec_python(
        self, script: str, timeout: int = 120
    ) -> subprocess.CompletedProcess[str]:
        """Execute a Python script inside the running container."""
        self.start()
        cmd = ["docker", "exec", "-i", self.container_name, "python3", "-c", script]
        return self._run(cmd, timeout=timeout, check=True)

    def exec_python_with_env(
        self, script: str, timeout: int = 120
    ) -> subprocess.CompletedProcess[str]:
        """Execute a Python script inside the running container with KiCad environment variables."""
        self.start()
        
        # Write script to a temporary file in the container
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(script)
            tmp_file_path = tmp_file.name
        
        try:
            # Copy the script to the container
            cp_cmd = ["docker", "cp", tmp_file_path, f"{self.container_name}:/tmp/temp_script.py"]
            self._run(cp_cmd, check=True)
            
            # Set up KiCad environment variables and execute the script
            env_setup = """
export KICAD5_SYMBOL_DIR=/usr/share/kicad/library
export KICAD5_FOOTPRINT_DIR=/usr/share/kicad/modules
"""
            
            cmd = [
                "docker",
                "exec",
                "-i",
                self.container_name,
                "bash",
                "-c",
                f"{env_setup}python3 /tmp/temp_script.py",
            ]
            return self._run(cmd, timeout=timeout, check=True)
        finally:
            # Clean up temporary files
            try:
                os.remove(tmp_file_path)
            except OSError:
                pass
            # Remove script from container
            rm_cmd = [
                "docker",
                "exec",
                "-i",
                self.container_name,
                "rm",
                "-f",
                "/tmp/temp_script.py",
            ]
            try:
                self._run(rm_cmd, check=True)
            except subprocess.CalledProcessError:
                pass

    def exec_erc(
        self, script_path: str, wrapper: str, timeout: int = 60
    ) -> subprocess.CompletedProcess[str]:
        """Copy a script and run ERC inside the container."""
        self.start()
        cp_cmd = ["docker", "cp", script_path, f"{self.container_name}:/tmp/script.py"]
        self._run(cp_cmd, check=True)
        cmd = ["docker", "exec", "-i", self.container_name, "python3", "-c", wrapper]
        try:
            return self._run(cmd, timeout=timeout, check=True)
        finally:
            rm_cmd = [
                "docker",
                "exec",
                "-i",
                self.container_name,
                "rm",
                "-f",
                "/tmp/script.py",
            ]
            try:
                self._run(rm_cmd, check=True)
            except subprocess.CalledProcessError:  # pragma: no cover - cleanup failure
                logging.error(
                    "Failed to remove temporary script in container %s",
                    self.container_name,
                )

    def exec_full_script(
        self, script_path: str, timeout: int = 180
    ) -> subprocess.CompletedProcess[str]:
        """Execute a full SKiDL script inside the container."""
        self.start()
        cp_cmd = ["docker", "cp", script_path, f"{self.container_name}:/tmp/script.py"]
        self._run(cp_cmd, check=True)
        cmd = [
            "docker",
            "exec",
            "-i",
            self.container_name,
            "python3",
            "/tmp/script.py",
        ]
        try:
            return self._run(cmd, timeout=timeout, check=True)
        finally:
            rm_cmd = [
                "docker",
                "exec",
                "-i",
                self.container_name,
                "rm",
                "-f",
                "/tmp/script.py",
            ]
            try:
                self._run(rm_cmd, check=True)
            except subprocess.CalledProcessError:  # pragma: no cover - cleanup failure
                logging.error(
                    "Failed to remove temporary script in container %s",
                    self.container_name,
                )

    def exec_full_script_with_env(
        self, script_path: str, timeout: int = 180
    ) -> subprocess.CompletedProcess[str]:
        """Execute a full SKiDL script inside the container with KiCad environment variables."""
        self.start()
        cp_cmd = ["docker", "cp", script_path, f"{self.container_name}:/tmp/script.py"]
        self._run(cp_cmd, check=True)

        # Set up KiCad environment variables for symbol library access
        env_setup = """
export KICAD5_SYMBOL_DIR=/usr/share/kicad/library
export KICAD5_FOOTPRINT_DIR=/usr/share/kicad/modules
"""

        cmd = [
            "docker",
            "exec",
            "-i",
            self.container_name,
            "bash",
            "-c",
            f"{env_setup}python3 /tmp/script.py",
        ]
        try:
            return self._run(cmd, timeout=timeout, check=True)
        finally:
            rm_cmd = [
                "docker",
                "exec",
                "-i",
                self.container_name,
                "rm",
                "-f",
                "/tmp/script.py",
            ]
            try:
                self._run(rm_cmd, check=True)
            except subprocess.CalledProcessError:  # pragma: no cover - cleanup failure
                logging.error(
                    "Failed to remove temporary script in container %s",
                    self.container_name,
                )

    def exec_erc_with_env(
        self, script_path: str, wrapper: str, timeout: int = 60
    ) -> subprocess.CompletedProcess[str]:
        """Copy a script and run ERC inside the container with KiCad environment variables."""
        self.start()
        cp_cmd = ["docker", "cp", script_path, f"{self.container_name}:/tmp/script.py"]
        self._run(cp_cmd, check=True)

        # Write wrapper script to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(wrapper)
            tmp_file_path = tmp_file.name
        
        try:
            # Copy the wrapper script to the container
            cp_wrapper_cmd = ["docker", "cp", tmp_file_path, f"{self.container_name}:/tmp/wrapper.py"]
            self._run(cp_wrapper_cmd, check=True)
            
            # Set up KiCad environment variables and execute the wrapper
            env_setup = """
export KICAD5_SYMBOL_DIR=/usr/share/kicad/library
export KICAD5_FOOTPRINT_DIR=/usr/share/kicad/modules
"""
            
            cmd = [
                "docker",
                "exec",
                "-i",
                self.container_name,
                "bash",
                "-c",
                f"{env_setup}python3 /tmp/wrapper.py",
            ]
            return self._run(cmd, timeout=timeout, check=True)
        finally:
            # Clean up temporary files
            try:
                os.remove(tmp_file_path)
            except OSError:
                pass
            # Remove scripts from container
            rm_cmd = [
                "docker",
                "exec",
                "-i",
                self.container_name,
                "rm",
                "-f",
                "/tmp/script.py",
                "/tmp/wrapper.py",
            ]
            try:
                self._run(rm_cmd, check=True)
            except subprocess.CalledProcessError:  # pragma: no cover - cleanup failure
                logging.error(
                    "Failed to remove temporary script in container %s",
                    self.container_name,
                )

    def copy_generated_files(self, container_pattern: str, host_dir: str) -> List[str]:
        """Copy files matching ``container_pattern`` to ``host_dir``."""
        self.start()
        ls_cmd = [
            "docker",
            "exec",
            self.container_name,
            "sh",
            "-c",
            f"ls {container_pattern} 2>/dev/null || true",
        ]
        proc = self._run(ls_cmd, check=True)
        files: List[str] = []
        for line in proc.stdout.splitlines():
            src = line.strip()
            if not src:
                continue
            dest = os.path.join(host_dir, os.path.basename(src))
            cp_cmd = ["docker", "cp", f"{self.container_name}:{src}", dest]
            try:
                self._run(cp_cmd, check=True)
                files.append(dest)
            except subprocess.CalledProcessError:
                logging.error("Failed to copy %s from container", src)
        return files

    def stop(self) -> None:
        """Stop and remove the container."""
        if not self.started:
            return
        subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
        self.started = False
