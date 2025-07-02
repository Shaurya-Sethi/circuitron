import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import circuitron.cli as cli
from circuitron.models import CodeGenerationOutput


class FakeResponse:
    def __init__(self, data: dict):
        self._data = data

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._data


def test_run_circuitron_invokes_backend():
    out = CodeGenerationOutput(complete_skidl_code="code")

    async def fake_post(url: str, json: dict) -> FakeResponse:
        assert "p" == json["prompt"]
        assert json["reasoning"] is True
        assert json["debug"] is False
        return FakeResponse({"stdout": "", "stderr": "", "result": out.model_dump()})

    client_mock = AsyncMock()
    client_mock.post.side_effect = fake_post
    client_cls = patch("httpx.AsyncClient", autospec=True)
    with client_cls as client_class:
        client_class.return_value.__aenter__.return_value = client_mock
        result = asyncio.run(cli.run_circuitron("p", show_reasoning=True))
    assert result == out


def test_cli_main_uses_args_and_prints(capsys):
    out = CodeGenerationOutput(complete_skidl_code="abc")
    args = SimpleNamespace(prompt="p", reasoning=False, debug=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)):
        cli.main()
    captured = capsys.readouterr().out
    assert "GENERATED SKiDL CODE" in captured
    assert "abc" in captured


def test_cli_main_prompts_for_input(monkeypatch):
    out = CodeGenerationOutput(complete_skidl_code="xyz")
    args = SimpleNamespace(prompt=None, reasoning=True, debug=True)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
        patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)) as run_mock:
        monkeypatch.setattr("builtins.input", lambda _: "hello")
        cli.main()
        run_mock.assert_awaited_with("hello", True, True)


def test_module_main_called():
    import runpy
    with patch("circuitron.cli.main") as main_mock:
        runpy.run_module("circuitron", run_name="__main__")
        main_mock.assert_called_once()
