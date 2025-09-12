import asyncio
import os
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
        tools_mod.execute_final_script(script, str(out_dir), "design")
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


def test_execute_final_script_filters_preexisting_files(tmp_path, monkeypatch):
    # Arrange: create some preexisting artifacts from an older session
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    old1 = out_dir / "led_9v_schematic.json"
    old2 = out_dir / "led_9v_schematic.svg"
    old1.write_text("OLD")
    old2.write_text("OLD")

    class FakeProc:
        def __init__(self) -> None:
            self.returncode = 0
            self.stdout = "ok"
            self.stderr = ""

    class FakeDockerSession:
        def __init__(self, _image: str, _name: str, volumes: Dict[str, str]):
            self.container_name = _name
            self.volumes = volumes

        def exec_full_script_with_env(self, script_path: str, timeout: int = 180):
            return FakeProc()

        def copy_generated_files(self, container_pattern: str, host_dir: str):
            # Simulate that the container has both old and new files,
            # but actually create only the new ones in the host dir.
            new1 = os.path.join(host_dir, "boost_converter.json")
            new2 = os.path.join(host_dir, "boost_converter.svg")
            with open(new1, "w", encoding="utf-8") as f:
                f.write("NEW")
            with open(new2, "w", encoding="utf-8") as f:
                f.write("NEW")
            # Return a list that includes old names to mimic a wide copy
            return [
                os.path.join(host_dir, "led_9v_schematic.json"),
                os.path.join(host_dir, "led_9v_schematic.svg"),
                new1,
                new2,
            ]

        def stop(self) -> None:
            pass

    # Patch DockerSession used inside execute_final_script
    from circuitron import tools as tools_mod

    monkeypatch.setattr(tools_mod, "DockerSession", FakeDockerSession)

    # Act
    result_json = asyncio.run(
    tools_mod.execute_final_script("from skidl import *\nERC()\n", str(out_dir), "design")
    )
    data = json.loads(result_json)

    # Assert: only the new files should be reported back
    returned = set(os.path.basename(p) for p in data.get("files", []))
    assert returned == {"boost_converter.json", "boost_converter.svg", "design.py"}
