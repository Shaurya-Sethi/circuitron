from rich.console import Console
from circuitron.ui.components import panel
from circuitron.ui.app import TerminalUI


def test_panel_renders_markup_in_output_summary(snapshot=None):
    """Ensure Rich markup tags are styled, not printed literally.

    We render a small Output Summary with markup and capture the console output.
    The output should not contain literal sequences like "[bold green]".
    """
    console = Console(file=None, record=True, force_terminal=True, width=80)

    content = "\n".join([
        "[bold green]Success[/]",
        "[dim]notes:[/] some detail",
    ])
    panel.show_panel(console, "Output Summary", content, render="markup")

    output = console.export_text()

    # No literal markup should be present
    assert "[bold green]" not in output
    # Shorthand closer should not appear either (export_text removes styling)
    assert "[dim]" not in output
    assert "[/]" not in output

    # Should include plain words styled (exported text strips styles), so check text presence
    assert "Success" in output
    assert "notes:" in output


def test_output_summary_escapes_stdout_stderr_markup_like_text():
    console = Console(file=None, record=True, force_terminal=True, width=80)
    ui = TerminalUI(console)

    files_dict = {
        "success": True,
        "stdout": "hello [not-a-tag] world",
        "stderr": "warn: check [this] detail",
        "files": [],
    }

    ui.display_files(files_dict)
    text = console.export_text()

    # The literal bracketed text should appear as-is in exported text
    assert "[not-a-tag]" in text
    assert "[this]" in text

