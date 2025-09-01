import asyncio
import os
import subprocess
from typing import Dict

import json

from circuitron.utils import prepare_output_dir
from circuitron import tools as tools_mod


def test_prepare_output_dir_preserves_existing_files(tmp_path):
    # Arrange: create a file in the directory
    out_dir = tmp_path / "circuitron_output"
    out_dir.mkdir()
    existing = out_dir / "old_result.net"
    existing.write_text("dummy")

    # Act: prepare_output_dir should not delete existing files
    result_dir = prepare_output_dir(str(out_dir))

    # Assert
    assert os.path.abspath(result_dir) == str(out_dir.resolve())
    assert existing.exists(), "Existing outputs must not be removed"


def test_execute_final_script_mounts_workspace_and_copies(tmp_path, monkeypatch):
    # Arrange
    captured: Dict[str, object] = {}

    class FakeProc:
        def __init__(self) -> None:
            self.returncode = 0
            self.stdout = "ok"
            self.stderr = ""

    class FakeDockerSession:
        def __init__(self, _image: str, _name: str, volumes: Dict[str, str]):
            # Capture host:container mapping and remember container mount path
            captured["volumes"] = volumes
            mount_values = list(volumes.values())
            assert len(mount_values) == 1
            captured["container_mount"] = mount_values[0]
            self.container_name = _name

        def exec_full_script_with_env(self, script_path: str, timeout: int = 180):
            # Verify the wrapper script changes directory to /workspace
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert f"os.chdir(\"{captured['container_mount']}\")" in content
            return FakeProc()

        def copy_generated_files(self, container_pattern: str, host_dir: str):
            # Verify we copy from the mounted directory
            assert container_pattern == f"{captured['container_mount']}/*"
            captured["copy_host_dir"] = host_dir
            # Pretend two artifacts were created
            return [
                os.path.join(host_dir, "design.net"),
                os.path.join(host_dir, "design.kicad_sch"),
            ]

        def stop(self) -> None:
            pass

    monkeypatch.setattr(tools_mod, "DockerSession", FakeDockerSession)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    script = "from skidl import *\nERC()\n"

    # Act
    result_json = asyncio.run(
        tools_mod.execute_final_script(script, str(out_dir), keep_skidl=False)
    )
    data = json.loads(result_json)

    # Assert behavior and response
    # Mount target may be a fixed '/workspace' or a converted '/mnt/<drive>/...' path.
    assert list(captured["volumes"].keys()) == [str(out_dir)]
    mount_target = list(captured["volumes"].values())[0]
    assert mount_target == "/workspace" or mount_target.startswith("/mnt/")
    assert captured["copy_host_dir"] == str(out_dir)
    assert data["success"] is True
    # Files should be absolute host paths under out_dir
    assert all(str(out_dir) in p for p in data.get("files", []))
