import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def test_cli_setup_subcommand_skips_kicad_and_calls_runner() -> None:
    import circuitron.cli as cli
    from circuitron.models import SetupOutput

    args = SimpleNamespace(
        command="setup",
        docs_url="https://devbisme.github.io/skidl/",
        repo_url="https://github.com/devbisme/skidl",
        timeout=None,
        dev=False,
    )

    out = SetupOutput(
        docs_url=args.docs_url,
        repo_url=args.repo_url,
        supabase_status="created",
        neo4j_status="created",
        operations=[],
        warnings=[],
        errors=[],
        elapsed_seconds=0.1,
    )

    with patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.cli.setup_environment"), \
         patch("circuitron.setup.run_setup", AsyncMock(return_value=out)) as run_mock, \
         patch("circuitron.tools.kicad_session.start") as start_mock:
        cli.main()
        run_mock.assert_awaited_once()
        start_mock.assert_not_called()

