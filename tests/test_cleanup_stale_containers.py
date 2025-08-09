import subprocess
from unittest.mock import patch

from circuitron.docker_session import cleanup_stale_containers


def test_cleanup_stale_containers_force_removes_running() -> None:
    ps_proc = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="abc cont1\ndef cont2\n", stderr=""
    )
    rm_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("subprocess.run", side_effect=[ps_proc, rm_proc]) as run_mock:
        cleanup_stale_containers("cont", "cont2")
    assert run_mock.call_args_list[0].args[0][:3] == ["docker", "ps", "-a"]
    assert run_mock.call_args_list[1].args[0][:3] == ["docker", "rm", "-f"]
    assert run_mock.call_args_list[1].args[0][3:] == ["abc"]
