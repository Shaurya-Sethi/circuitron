import subprocess
import threading
from unittest.mock import patch

import pytest

from circuitron.docker_session import DockerSession


def test_reuse_running_container() -> None:
    session = DockerSession("img", "cont")
    proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="Up 3s\n", stderr="")
    with patch.object(session, "_run", return_value=proc) as run_mock:
        session.start()
        assert session.started is True
        run_mock.assert_called_once()
        assert run_mock.call_args.args[0][:3] == ["docker", "ps", "-a"]


def test_remove_exited_container() -> None:
    session = DockerSession("img", "cont")
    ps_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="Exited (0) 1s\n", stderr="")
    rm_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    run_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch.object(session, "_run", side_effect=[ps_proc, rm_proc, run_proc]) as run_mock:
        session.start()
        assert session.started is True
        assert run_mock.call_args_list[0].args[0][:3] == ["docker", "ps", "-a"]
        assert run_mock.call_args_list[1].args[0][:3] == ["docker", "rm", "-f"]
        assert run_mock.call_args_list[2].args[0][0] == "docker" and run_mock.call_args_list[2].args[0][1] == "run"


def test_start_logs_failure() -> None:
    session = DockerSession("img", "cont")
    ps_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    err = subprocess.CalledProcessError(returncode=1, cmd=["docker"], stderr="boom")
    with patch.object(session, "_run", side_effect=[ps_proc, err]) as run_mock, patch("circuitron.docker_session.logging.error") as log_mock:
        with pytest.raises(RuntimeError):
            session.start()
        log_mock.assert_called_once()
        assert run_mock.call_count == 2


def test_start_error_message() -> None:
    session = DockerSession("img", "cont")
    ps_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    err = subprocess.CalledProcessError(returncode=1, cmd=["docker"], stderr="boom")
    with patch.object(session, "_run", side_effect=[ps_proc, err]), patch("circuitron.docker_session.logging.error"):
        with pytest.raises(RuntimeError) as info:
            session.start()
        assert "Docker" in str(info.value)


def test_concurrent_start() -> None:
    session = DockerSession("img", "cont")
    ps_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    run_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch.object(session, "_run", side_effect=[ps_proc, run_proc]) as run_mock:
        t1 = threading.Thread(target=session.start)
        t2 = threading.Thread(target=session.start)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        assert session.started is True
        assert run_mock.call_count == 2
