# Circuitron CLI UI/UX Rework Plan

## 1. Analysis

### 1.1 Code Review
- **Mixed rendering paths.** Many modules call `print()` or `Console().print` directly instead of routing output through `TerminalUI` (`circuitron/cli.py` lines 35–74, `circuitron/utils.py` lines 158–205). This leads to inconsistent styles and makes the UI difficult to maintain.
- **Sparse progress feedback.** `Spinner` and `StatusBar` exist but are not used everywhere. Long running operations such as validation or ERC handling sometimes print plain text instead of showing a spinner (`pipeline.py` around line 240).
- **Repeated information.** The pipeline prints file locations and summaries multiple times (`pipeline.py` lines 523–726), cluttering the console.

### 1.2 Screenshot Observations
The `cli-ui-images` folder illustrates the current look and feel:
- `Screenshot 2025-07-13 172901.png` shows a large ASCII banner and a minimal prompt. The banner occupies most of the first screen.
- `Screenshot 2025-07-13 173001.png` and `173059.png` display the feedback form in plain text with dashed separators.
- `Screenshot 2025-07-13 173329.png` reveals component tables of different widths.
- `Screenshot 2025-07-13 173652.png` and `174504.png` show generated code rendered line‑by‑line inside individual boxes, making the code hard to read.
- `Screenshot 2025-07-13 174448.png` shows error messages mixed with normal output, all in the same color.

## 2. Identified Issues
1. **Inconsistent UI rendering.** Direct print statements bypass existing components, so panels, tables and plain text all appear with different formatting.
2. **Poor readability and information overload.** Dense blocks of text and boxed code (screenshots `173652.png`–`174534.png`) overwhelm the user.
3. **Unclear visual hierarchy.** Errors, warnings and status messages look the same (e.g. screenshot `174448.png`).
4. **Inefficient use of space.** The large banner and per‑line code boxes waste vertical space.
5. **Limited user feedback during long tasks.** Spinners do not cover every stage, leaving the user uncertain about progress.
6. **Inconsistent table layout and sizing.** Search result tables vary in width (screenshot `173329.png`).

## 3. Proposed Improvements
- **Centralize all output through `TerminalUI`.** Replace raw `print()` calls with methods like `display_info`, `display_warning`, and `display_error`. This ensures uniform styling and makes it easy to change themes.
- **Adopt Rich features for readability.** Use `rich.syntax.Syntax` inside a single panel for code blocks, `rich.table.Table` with consistent column widths for search results, and `Panel` or `Text` styles to clearly mark errors and warnings.
- **Simplify the banner.** Reduce its height or show it only once per session so that the prompt and status bar remain visible.
- **Improve progress indicators.** Extend the `Spinner` component to wrap every network or agent call, showing elapsed time just like modern CLI tools.
- **Structure the feedback form.** Present questions and inputs in a bordered panel or form component instead of plain dashed lines.
- **Consolidate final output.** Display one summary panel with links to generated files and a separate nicely formatted validation/ERC summary.

## 4. Detailed Implementation Plan
### 4.1 Centralize UI Control in `TerminalUI`
- Refactor `circuitron/cli.py` and `circuitron/ui/app.py` to remove direct `Console().print` calls.
- Add `display_info`, `display_warning`, `display_error`, `display_code`, and `display_generated_files_summary` helpers.
- Route all prints from `utils.py` through these helpers.

### 4.2 Enhance UI Components
- Create `input_box.py` for user prompts.
- Add `code_panel.py` for syntax‑highlighted code display.
- Implement `message_panel.py` to standardize informational, warning, and error panels.
- Rework `tables.py` so component results share the same width and style.
- Ensure `Spinner` and `StatusBar` are active for every stage of the pipeline.

### 4.3 Refactor Flow and Content
- Remove duplicated plan and validation summaries.
- Present validation results and ERC tables in a compact, readable format.
- Replace emoji markers with clean text and color cues for professionalism.

## 5. Implementation Roadmap
1. **Phase 1 – Core refactoring.** Introduce the new `TerminalUI` methods and replace all direct prints.
2. **Phase 2 – Component integration.** Implement new components and update existing screens.
3. **Phase 3 – Flow cleanup.** Eliminate duplicate output and redesign the final summary.
4. **Phase 4 – Testing and refinement.** Ensure the new UI meets the standards outlined above and iterate based on feedback.

Applying these changes will modernize the Circuitron CLI, provide a professional appearance, and give users clear feedback throughout the design process.
