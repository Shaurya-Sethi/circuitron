# Circuitron CLI: A Blueprint for a Stunning Terminal UI/UX

## 1. Vision & Core Principles

This document outlines a comprehensive architectural plan to refactor and elevate the Circuitron CLI, transforming it into a state-of-the-art, intuitive, and visually stunning terminal-based user experience. We will move beyond simple text outputs to a rich, interactive, and "electric" interface that is both beautiful and functional.

Our design will be guided by five core principles, inspired by the `gemini-cli-ui-ux-blueprint.md` and tailored for Circuitron's unique workflow:

1.  **Component-Driven Architecture:** Decompose the UI into modular, reusable components (`Panel`, `Spinner`, `Prompt`, etc.) to ensure consistency and maintainability. This mirrors best practices from modern UI frameworks.
2.  **Comprehensive Theming:** Implement a robust theming system that goes beyond the banner. Every UI element, from borders to text, will be theme-aware, allowing for deep customization and a cohesive "electric" aesthetic.
3.  **Interactive & Intelligent Prompt:** Replace the basic `input()` with a powerful, full-featured prompt that supports history, validation, and context-aware autocompletion.
4.  **Rich, Contextual Output:** Structure all output within styled panels. Leverage Markdown for formatted text, syntax highlighting for code, and custom components for displaying specific data types like part lists or validation results.
5.  **Dynamic, Asynchronous Feedback:** Provide persistent, real-time feedback on the application's state through a dedicated status bar, dynamic spinners with context, and non-blocking notifications.

## 2. Proposed UI Architecture

The new UI will be built around a central `TerminalUI` class in `circuitron/ui/app.py`. This class will manage the layout, theming, and rendering of all components.

### 2.1. Directory Structure

```
circuitron/
└── ui/
    ├── __init__.py
    ├── app.py          # Main TerminalUI class, layout management
    ├── themes.py       # ThemeManager and color palette definitions
    └── components/
        ├── __init__.py
        ├── banner.py       # ASCII art and gradient logic
        ├── prompt.py       # Interactive user input component
        ├── panel.py        # Generic content panel
        ├── spinner.py      # Enhanced status spinner
        ├── status_bar.py   # Persistent footer
        └── tables.py       # For structured data like part lists
```

### 2.2. The `TerminalUI` Class

The `TerminalUI` class in `app.py` will be the heart of the UI. It will be responsible for:

*   **Initialization:** Setting up the layout, theme, and initial state.
*   **Rendering:** Drawing all components to the screen.
*   **State Management:** Acting as the single source of truth for UI state (e.g., current stage, spinner text, status messages).
*   **Component Integration:** Providing methods to display different UI elements (`show_panel`, `get_prompt_input`, etc.).

## 3. Detailed Component Breakdown

### 3.1. Theming Engine (`themes.py`)

The theming system will be managed by a `ThemeManager` class.

*   **Palettes:** Define multiple theme palettes (e.g., `ELECTRIC_NEON`, `TERMINAL_DARK`, `HIGH_CONTRAST`) as dataclasses or dictionaries. Each theme will define a consistent set of colors for backgrounds, foregrounds, accents, errors, etc.
*   **ThemeManager:** A singleton class to manage the active theme. It will have methods like `set_theme()`, `get_theme()`, and `get_color()`.
*   **Persistence:** The selected theme will be saved to a user-specific configuration file (e.g., `~/.circuitron/config.json`).
*   **`NO_COLOR` Support:** The `ThemeManager` will automatically detect the `NO_COLOR` environment variable and return a colorless theme.

**Example Theme Definition:**

```python
# in circuitron/ui/themes.py
from dataclasses import dataclass

@dataclass
class ColorPalette:
    background: str
    foreground: str
    accent1: str
    accent2: str
    error: str
    # ... and so on

ELECTRIC_NEON = ColorPalette(
    background="#0a0a1a",
    foreground="#d0d0ff",
    accent1="#00f0ff",
    accent2="#ff00ff",
    error="#ff4040",
)
```

### 3.2. Interactive Prompt (`prompt.py`)

We will replace the standard `input()` with a custom prompt component built using `prompt_toolkit`.

*   **Features:**
    *   **History:** Persistent command history across sessions.
    *   **Key Bindings:** Standard readline-style key bindings (Ctrl+A, Ctrl+E, etc.).
    *   **Styling:** The prompt will be styled using the active theme.
    *   **Validation:** Support for real-time input validation.
    *   **Multi-line Input:** Easy multi-line input with `Shift+Enter` or similar.
*   **Integration:** The `TerminalUI` will have a `prompt()` method that displays the styled prompt and returns the user's input.

### 3.3. Rich Output & Panels (`panel.py`, `tables.py`)

All output will be displayed within `rich.panel.Panel` instances to ensure consistent styling and layout.

*   **Generic Panel:** A `Panel` component that takes a title and content (string, `rich` renderable, etc.) and displays it with themed borders and title styling.
*   **Markdown Rendering:** Use `rich.markdown.Markdown` to render formatted text, ensuring that explanations and rationales are easy to read.
*   **Syntax Highlighting:** Code blocks within Markdown will be automatically syntax-highlighted.
*   **Structured Data:** For tabular data like part lists or validation results, we will use `rich.table.Table` to create beautifully formatted tables within panels.

**Example Usage:**

```python
# in circuitron/cli.py
ui.show_panel(
    title="Design Plan",
    content=Markdown(design_plan_markdown),
    accent_color="accent1" # Key from the theme palette
)
```

### 3.4. Dynamic Feedback (`spinner.py`, `status_bar.py`)

*   **Enhanced Spinner:** The `StageSpinner` will be enhanced to show:
    *   The current stage name.
    *   Elapsed time.
    *   A rotating list of contextual phrases (e.g., "Analyzing schematics...", "Contacting component suppliers...").
*   **Persistent Status Bar:** A status bar will be displayed at the bottom of the screen at all times. It will show:
    *   The current major pipeline stage (e.g., "PLANNING", "DESIGN", "VERIFICATION").
    *   The active theme.
    *   Any active modes (e.g., `--auto-accept`).
    *   Session-specific information like token usage.

## 4. High-Level Implementation Plan

1.  **Foundation (`app.py`, `themes.py`):**
    *   Implement the `ThemeManager` and define the initial themes.
    *   Create the main `TerminalUI` class and the basic layout structure.
    *   Implement the startup banner, ensuring it displays *before* any prompts.

2.  **Output Refactoring (`panel.py`, `tables.py`):**
    *   Create the generic `Panel` and `Table` components.
    *   Go through the existing codebase and replace all `print()` statements with calls to the new `ui.show_panel()` or `ui.show_table()` methods.

3.  **Input Refactoring (`prompt.py`):**
    *   Implement the `prompt_toolkit`-based input component.
    *   Replace all `input()` calls with the new `ui.prompt()` method.

4.  **Dynamic Feedback (`spinner.py`, `status_bar.py`):**
    *   Enhance the `StageSpinner` with the new features.
    *   Implement the persistent `StatusBar` and integrate it into the main layout.

5.  **Integration and Testing:**
    *   Thoroughly test all new UI components and their integration with the core Circuitron logic.
    *   Update documentation to reflect the new UI and its features.

By following this plan, we will create a CLI experience for Circuitron that is not only highly functional but also a pleasure to use, setting a new standard for terminal-based AI agents.