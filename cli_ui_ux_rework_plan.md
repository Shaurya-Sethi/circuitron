# Circuitron CLI UI/UX Rework Plan

## Current Implementation Analysis

### CLI Logo
- **Source:** `logo.py` defines `LOGO_ART` and `apply_gradient()` with a set of color themes.
- **Display:** `TerminalUI.start_banner()` prints the gradient logo using `rich` and the default `ELECTRIC_THEME`.
- **Issue:** In `cli.py`, the CLI prompts for user input **before** the logo is shown (`prompt = args.prompt or input("Prompt: ")`), breaking the expected flow.

### Prompt and User Interaction
- User prompt collected via Python `input()` calls (`cli.py` and `utils.collect_user_feedback`).
- No structured prompt widget or history; plain `"Prompt: "` text appears before any branding.
- Follow‑up questions and edits use sequential `input()` loops with simple text labels ("Your answer:" etc.).

### Colors, Borders & Spacing
- Rich is only used for the banner gradient and progress spinner messages.
- Outputs such as plan sections, part lists and validation messages rely on uncolored `print()` statements and ASCII separators (`===`, `---`).
- No consistent use of panels, boxes or themed colors from `ui/themes.py` beyond the banner.

### Spinner / Loading Indicators
- `StageSpinner` (in `ui/components/progress.py`) wraps `rich.status.Status` with a dots spinner.
- Spinner text is `[bold cyan]{stage}...` while running and `[green]{stage} complete` when finished.
- Only one spinner instance; no elapsed time or multiple concurrent indicators.

### Visual Feedback Across Stages
- Each pipeline step prints raw text results after completion via helper functions in `utils.py`.
- User approval loop shows plain text prompts without any color cues or layout.
- No footer area for persistent status, no theme switching, no responsive layout logic.

## Blueprint Comparison
The `gemini-cli-ui-ux-blueprint.md` describes a richer experience:
- Gradient ASCII banner on startup with theme manager support【F:gemini-cli-ui-ux-blueprint.md†L19-L23】【F:gemini-cli-ui-ux-blueprint.md†L41-L44】.
- Structured input prompt supporting history navigation and shell mode with keybindings (Ctrl+A/E/L/P/N)【F:gemini-cli-ui-ux-blueprint.md†L45-L60】.
- Spinners and streaming state indicators in a footer area【F:gemini-cli-ui-ux-blueprint.md†L67-L69】.
- Bordered boxes, markdown rendering, and color‑themed output for messages【F:gemini-cli-ui-ux-blueprint.md†L61-L66】【F:gemini-cli-ui-ux-blueprint.md†L82-L90】.
- Commands such as `/theme` to switch palettes and an overlay help menu【F:gemini-cli-ui-ux-blueprint.md†L70-L78】.
- Responsive sizing, `NO_COLOR` mode and theme objects controlling palettes【F:gemini-cli-ui-ux-blueprint.md†L143-L170】.

Our current CLI only partially meets these expectations (banner and basic spinner) and lacks theme management, structured prompts, dynamic feedback and layout elements.

## Rework Objectives
1. **Proper Launch Flow**
   - Show the gradient Circuitron logo immediately when the CLI starts, *before* requesting the design prompt.
   - Display a brief tagline or instructions under the logo (e.g., "Enter a design request or type `/help` for options").

2. **Theme System & Electric Branding**
   - Expand `ui/themes.py` into a theme manager class similar to the blueprint's `ThemeManager`. Include default "electric" theme plus additional palettes (dark, light, high‑contrast).
   - Allow switching themes via a `/theme` command. Persist choice in a small config file (e.g., using `pathlib.Path.home()/".circuitron"`).
   - Respect `NO_COLOR` environment variable for colorless terminals.

3. **Structured Prompt Component**
   - Replace plain `input()` with a Rich or `prompt_toolkit` based prompt supporting history and basic editing shortcuts (Ctrl+A/E/L/P/N). Display inside a rounded box with accent colors from the active theme.
   - Keep prompts consistent during plan feedback (open questions, edit requests, additional requirements). Use the same component to reduce code repetition.
   - Consider shell mode support (`!` prefix) for executing commands as in the blueprint.

4. **Output Layout Enhancements**
   - Use `rich.panel.Panel` or `textual` widgets to wrap plan sections, part lists, and validation results in bordered boxes. Apply theme accent colors for titles and dividers.
   - Parse and display markdown (e.g., design rationale, documentation snippets) using `rich.markdown.Markdown` with syntax highlighting for code blocks.
   - Limit output width to ~90% of terminal width and reflow when the terminal is resized.

5. **Spinners & Dynamic Feedback**
   - Extend `StageSpinner` to show elapsed time and optional custom phrases while waiting, inspired by `LoadingIndicator` and `usePhraseCycler` from the blueprint.
   - Maintain a footer/status bar component displaying current stage, token counts, and any special modes (auto‑accept, shell mode). Update it via a shared context object.

6. **Consistent Color & Typography**
   - Adopt accent colors from the theme for headings (`bold`), subheadings (`italic`) and warnings/errors (`red` or theme accent). Remove bare `print()` separators in favor of styled text and panels.
   - Ensure spacing around sections is handled with small padding/margins—avoid excessive blank lines.

7. **UX Interaction Improvements**
   - Provide clear instructions during the plan review loop (e.g., numbered questions with input prompts below). Confirm choices with colored check marks or symbols.
   - After generating files, list them as clickable links using Rich markup, grouped in a panel with a success message.
   - Optional: support `/help` command to list shortcuts and features.

8. **Optional Enhancements**
   - Explore `textual` for a fully reactive layout with keyboard navigation if Rich widgets become limiting.
   - Add simple animations (e.g., progress bar filling) for longer operations.
   - Consider a light/dark theme toggle based on terminal background detection.

## Implementation Steps (High Level)
1. **Refactor CLI Entry (`cli.py`)**
   - Initialize `TerminalUI` first and call `ui.start_banner()` immediately.
   - Use `ui.prompt_user()` (new function) to collect the initial design prompt.
2. **Expand `TerminalUI`**
   - Create methods for displaying panels (`show_plan`, `show_parts`, `show_validation`, etc.).
   - Integrate a footer/status context and spinner updates.
3. **Introduce Theme Manager**
   - Define theme objects with palette values; implement a singleton to retrieve active colors.
   - Provide CLI command `/theme` to switch and persist themes.
4. **Update Pipeline Functions**
   - Pass `ui` instance throughout; use new display helpers instead of raw prints.
   - Add callbacks/events for progress updates and error handling.
5. **Testing & Docs**
   - Update unit tests to mock new UI methods and verify they are called appropriately.
   - Document usage and screenshot examples in `README.md` once implementation stabilizes.

By aligning the CLI with these design principles, Circuitron will deliver a futuristic, electric-themed terminal experience consistent with the blueprint while remaining functional and user-friendly.
