# Circuitron Terminal UI Architecture Plan

## Current CLI Overview

Circuitron currently exposes a simple command line interface in `circuitron/cli.py`. The `main()` function parses flags, verifies containers, and executes the agentic pipeline via `run_circuitron()`. Output is printed directly to stdout. Important characteristics include:

- Entry point defined in `pyproject.toml` as `circuitron.cli:main`.
- `run_circuitron()` calls `pipeline.run_with_retry()` and returns a `CodeGenerationOutput`.
- Pipeline steps (`run_planner`, `run_part_finder`, etc.) print their results using helper functions in `utils.py`.
- The CLI supports optional flags such as `--dev`, `--reasoning`, `--retries`, and `--output-dir`.
- There is no interactive UI; users supply a prompt and view plain text output.

This approach is functional but lacks branding, progress indicators, and an intuitive navigation model. Usability is limited to sequential text without spinners or rich formatting.

## UI/UX Blueprint Requirements

The `gemini-cli-ui-ux-blueprint.md` file describes a modern terminal experience with features like a startup banner, theme manager, input prompt handling, status indicators and dynamic feedback. Key excerpts include:

- "Uses ASCII art from `AsciiArt.ts` with color gradients applied through the active theme"【F:gemini-cli-ui-ux-blueprint.md†L19-L21】.
- "`LoadingIndicator` shows a spinner and elapsed time while waiting"【F:gemini-cli-ui-ux-blueprint.md†L67-L69】.
- Step‑by‑step project layout suggests a `ui` directory with components, themes, contexts and hooks【F:gemini-cli-ui-ux-blueprint.md†L143-L149】.
- Prompt handling includes history navigation and shell mode with key bindings【F:gemini-cli-ui-ux-blueprint.md†L45-L60】.

These guidelines emphasize clear visual feedback, themeable colors, and interactive controls.

## Desired CLI Features

The new CLI should launch with the command `circuitron` without additional flags. It will display the Circuitron banner from `logo.py` using the "electric" theme and follow an electric visual style throughout the run. Required features:

1. **Branding** – Gradient logo on startup and consistent color palette.
2. **Progress Indicators** – Animated spinners for each pipeline stage (Planning, Editing, Looking for Parts, Coding, etc.).
3. **Stepwise Outputs** – Display of:
   - Initial/edited plan
   - Selected list of parts
   - Validated SKiDL code
   - Links to netlist, SVG, KiCad schematic and PCB files
   - Nicely formatted netlist at the end
4. **Interactivity** – User approval loop and navigation should feel natural with no flags required at startup.
5. **Electric Theme** – Colors inspired by the "electric" theme in `logo.py` and optional dark/light theme switching similar to Gemini's blueprint.

## Proposed Architecture

### High‑Level Design

1. **UI Package** – Create `circuitron/ui/` with submodules:
   - `components/` – spinner widget, plan display, parts table, file links, etc.
   - `themes.py` – defines electric and other color themes, modeled after the blueprint.
   - `app.py` – orchestrates layout: banner, history list, prompt area, status bar.
   - `context.py` – maintains streaming state (e.g., current stage, elapsed time).
2. **Terminal UI Manager** – A `TerminalUI` class will encapsulate Rich/Textual logic. It exposes `start_stage(name)`, `finish_stage(name, data)`, `display_message(text, style)` and similar helpers.
3. **Integration Layer** – Modify `pipeline.py` to emit events or accept a callback so `TerminalUI` can update spinners and display outputs without rewriting pipeline logic. Example:
   ```python
   async def run_planner(prompt: str, ui: TerminalUI | None = None) -> RunResult:
       if ui:
           ui.start_stage("Planning")
       result = await run_agent(planner, sanitize_text(prompt))
       if ui:
           ui.finish_stage("Planning", result.final_output)
       return result
   ```
4. **CLI Entry Point** – Replace the existing CLI with a new command that initializes `TerminalUI`, runs the pipeline, and handles user input/feedback within the UI. The entry point remains `circuitron.cli:main` for compatibility.
5. **Logo Display** – Use `logo.apply_gradient()` with the "electric" theme to render the ASCII logo at startup.
6. **Spinner & Progress Implementation** – Leverage `rich`'s `Progress` and `Spinner` classes (or `textual` widgets) for animated indicators. Each pipeline step begins with a spinner that persists until the step completes.
7. **Formatted Output Panels** – Use `rich.panel.Panel`, `rich.table.Table`, and `rich.markdown.Markdown` to present plans, part lists and code blocks. File paths will be printed as clickable links using `console.print(f"[link=file://{path}]{name}[/]")`.
8. **User Interaction** – Incorporate `Prompt` component or `rich.prompt` to collect plan edits and open‑question answers. History and shortcuts follow the blueprint's guidance on key bindings.

### Module/Function Responsibilities

- `circuitron/ui/app.py`
  - `TerminalUI.run(prompt: str)` – Main method executing the pipeline and updating widgets.
  - `start_banner()` – Displays gradient logo.
  - `display_plan(plan: PlanOutput)` – Show initial design plan with navigation keys to continue.
  - `collect_feedback(plan: PlanOutput)` – Interactive form for user edits.
  - `display_files(files: list[str])` – List produced files with clickable links.
- `circuitron/ui/components/progress.py` – Helper for stage spinners.
- `circuitron/ui/themes.py` – Defines color palettes and theme manager. Mimic blueprint’s example theme object structure.

### Dependencies

- **rich** – Already used in `logo.py`; provides spinners, panels, tables and markdown rendering.
- **textual** (optional) – For more complex interactive layouts if needed.
- Optionally `prompt_toolkit` for advanced input editing/history if the built‑in features of `rich` are insufficient.

### Mapping Current → Future State

| Current Implementation | Future Implementation |
|-----------------------|-----------------------|
|Plain console printing through `print()` calls|Rich/Textual widgets for structured output|
|No progress feedback|`TerminalUI` shows spinners per stage|
|Arguments required for prompt|Interactive prompt with no flags| 
|Results shown as raw text|Themed panels with clickable file links|

Major architectural changes include adding an event/callback layer in `pipeline.py` and migrating CLI logic into a new `TerminalUI` class.

### Risks & Considerations

- **Asynchronous Flow** – Pipeline functions are `async`; the UI must handle concurrency without blocking Rich’s event loop.
- **Refactoring Scope** – Injecting UI callbacks requires careful updates to tests and pipeline signatures.
- **Terminal Compatibility** – Some terminals may not support color or hyperlinks; provide a `NO_COLOR` environment option as recommended in the blueprint【F:gemini-cli-ui-ux-blueprint.md†L168-L170】.
- **Dependency Footprint** – Textual adds weight; evaluate if Rich alone suffices before adopting another dependency.

## Recommended Next Steps

1. Prototype a minimal `TerminalUI` using Rich that wraps the existing pipeline without altering logic.
2. Incrementally refactor pipeline functions to accept an optional UI callback object.
3. Mirror Gemini CLI’s directory layout (`ui/components`, `ui/themes`, etc.) to keep the structure extensible.
4. Update unit tests to simulate UI callbacks and verify spinners start/stop as expected.
5. Expand documentation with usage examples and screenshots once the new interface is implemented.

---
