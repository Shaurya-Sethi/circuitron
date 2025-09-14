from pydantic import ValidationError

from circuitron.models import SetupOutput


def test_setup_output_constructs() -> None:
    out = SetupOutput(
        docs_url="https://devbisme.github.io/skidl/",
        repo_url="https://github.com/devbisme/skidl",
        supabase_status="created",
        neo4j_status="skipped",
        operations=["crawl docs", "skip repo"],
        warnings=["note"],
        errors=[],
        elapsed_seconds=1.23,
    )
    assert out.supabase_status == "created"
    assert out.neo4j_status == "skipped"


def test_setup_output_forbids_extra_fields() -> None:
    try:
        SetupOutput(
            docs_url="https://devbisme.github.io/skidl/",
            repo_url="https://github.com/devbisme/skidl",
            supabase_status="created",
            neo4j_status="created",
            operations=[],
            warnings=[],
            errors=[],
            elapsed_seconds=0.0,
            extra_field="nope",  # type: ignore[arg-type]
        )
    except ValidationError:
        # expected
        return
    assert False, "extra fields must be rejected"

