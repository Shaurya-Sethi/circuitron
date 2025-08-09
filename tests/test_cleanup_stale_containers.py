import subprocess
from unittest.mock import patch

from circuitron.docker_session import cleanup_stale_containers


def test_cleanup_force_removes_all_matching_containers() -> None:
    ps_proc = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="pref-1\npref-2\n", stderr=""
    )
    rm_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch(
        "circuitron.docker_session.subprocess.run",
        side_effect=[ps_proc, rm_proc, rm_proc],
    ) as run_mock:
        cleanup_stale_containers("pref-")
        assert run_mock.call_args_list[0].args[0][:3] == ["docker", "ps", "-aq"]
        assert run_mock.call_args_list[1].args[0][:3] == ["docker", "rm", "-f"]
        assert run_mock.call_args_list[2].args[0][:3] == ["docker", "rm", "-f"]


def test_cleanup_excludes_current_container() -> None:
    ps_proc = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="pref-1\npref-2\n", stderr=""
    )
    rm_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch(
        "circuitron.docker_session.subprocess.run",
        side_effect=[ps_proc, rm_proc],
    ) as run_mock:
        cleanup_stale_containers("pref-", "pref-2")
        assert run_mock.call_count == 2
        assert run_mock.call_args_list[1].args[0][-1] == "pref-1"
