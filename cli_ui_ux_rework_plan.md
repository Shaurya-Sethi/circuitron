# Circuitron CLI UI/UX Rework Plan

## 1. Analysis of Current UI/UX

Based on user feedback, analysis of UI screenshots, and a review of the codebase, the current CLI implementation suffers from several key issues:

*   **Inconsistent UI Rendering:** The application mixes direct `print()` calls with `rich`-based components, leading to a disjointed and unprofessional user experience. For example, some output is presented in formatted panels, while other text (like error messages and final output summaries) is printed directly to the console.
*   **Poor Readability and Information Overload:** Large blocks of text, such as the design plan and generated code, are presented as dense walls of text, making them difficult to read and understand. The final SKiDL code output is particularly problematic, with each line being boxed individually.
*   **Lack of Professionalism:** The UI uses emojis and has an inconsistent visual style, which detracts from the professional quality of the tool.
*   **Limited User Feedback:** Spinners and other progress indicators are used inconsistently, leaving the user unsure of the application's status during long-running operations.
*   **Duplicated Information:** Some information, like the design plan and validation summaries, appears to be displayed multiple times, leading to confusion.
*   **Inconsistent Component Sizing:** The tables used to display component search results have varying sizes, which looks unprofessional.

## 2. Proposed UI/UX Rework Plan

To address these issues, I propose a comprehensive rework of the CLI's UI/UX, focusing on the following principles:

*   **Centralized UI Management:** All UI rendering will be managed by the `TerminalUI` class in `circuitron/ui/app.py`. This will ensure a consistent look and feel across the entire application.
*   **Component-Based Architecture:** We will expand the existing component system in `circuitron/ui/components/` to create a standardized set of UI elements for all output.
*   **Professional and Clean Aesthetic:** The new UI will adopt a clean, professional design with consistent formatting, spacing, and color usage. Emojis will be removed.

### 2.1. Detailed Implementation Plan

#### 2.1.1. Centralize UI Control in `TerminalUI`

*   **Eliminate Direct `print()` Calls:** Refactor `circuitron/cli.py` and `circuitron/ui/app.py` to remove all direct `Console().print` calls for UI purposes. All UI rendering will be delegated to the `TerminalUI` class.
    *   **`circuitron/cli.py` specific changes:**
        *   Route `Console().print(f"Fatal error: {exc}", style="red")` in `run_circuitron` through `TerminalUI.display_error()`.
        *   Route `Console().print(f"Failed to start KiCad container: {exc}", style="red")` in `verify_containers` through `TerminalUI.display_error()`.
        *   Route `ui.console.print("\nExecution interrupted by user.", style="red")` and `ui.console.print(f"Error during execution: {exc}", style="red")` in `main` through `TerminalUI.display_error()`.
        *   Consolidate the final three `ui.console.print` calls for "Generated files have been saved..." into a new `TerminalUI.display_generated_files_summary()` method.
        *   Replace `panel.show_panel(ui.console, "Generated SKiDL Code", code_output.complete_skidl_code, ui.theme)` with `TerminalUI.display_code()`.
    *   **`circuitron/ui/app.py` specific changes:**
        *   Route `self.console.print("[bold]Type /help for commands[/bold]\n", style=self.theme.accent)` in `start_banner` through a new `TerminalUI.display_info()` method or integrate into the banner component.
        *   Route `self.console.print(f"Theme switched to {parts[1]}", style=self.theme.accent)` and `self.console.print(f"Available themes: {', '.join(theme_manager.available_themes())}", style=self.theme.accent)` in `set_theme` through `TerminalUI.display_info()`.
        *   Route `self.console.print("Available commands: /theme <name>, /help", style=self.theme.accent)` in `prompt_user` through `TerminalUI.display_info()`.
*   **Expand `TerminalUI` Functionality:** Add new methods to the `TerminalUI` class to handle all types of UI output, including informational messages (`display_info`), warnings (`display_warning`), errors (`display_error`), and progress indicators.

#### 2.1.2. Enhance UI Components

*   **Formatted User Input:** Create a new component, `input_box.py`, to provide a visually distinct and nicely formatted box for all user input prompts. The existing `circuitron/ui/components/prompt.py` will be refactored or replaced by this new component.
*   **Consistent Spinners:** Implement a global spinner manager or enhance the existing `Spinner` component to ensure that a spinner is displayed for all long-running operations, providing clear feedback to the user.
*   **Unified Component Table:** Rework the `tables.py` component to display a single, unified table for all component search results. The table will have a fixed width and consistent formatting.
*   **Formatted Code Display:** Create a new component, `code_panel.py`, specifically for displaying code. This component will use `rich.syntax.Syntax` for proper syntax highlighting and will present the code in a clean, readable format within a single panel.
*   **Standardized Message Panels:** Create a new component, `message_panel.py`, for displaying all informational messages, warnings, and errors. This component will use different styles (e.g., colors, icons) to distinguish between different message types.

#### 2.1.3. Refactor Application Flow and Output

*   **Eliminate Duplicate Output:** Review the application's control flow to identify and remove any instances of duplicate information being displayed. Specifically, address the potential duplicate display of the design plan (initial display vs. updated plan).
*   **Refactor `circuitron/utils.py` for UI Consistency:**
    *   **`collect_user_feedback`:** This function needs a complete overhaul. It should no longer directly print `Panel` or `Text`. Instead, it should utilize new `TerminalUI` methods for displaying questions, prompts, and feedback sections. The input mechanism should leverage the new `input_box.py` component.
    *   **`display_erc_results`:** Refactor to use a `TerminalUI` method (e.g., `display_erc_results_panel`) that leverages `message_panel.py` for consistent display. The raw JSON output should be formatted into a readable table or structured text.
    *   **`display_validation_summary`:** Refactor to use a `TerminalUI` method (e.g., `display_validation_summary_panel`) that leverages `message_panel.py`.
    *   **`display_warnings` and `display_errors`:** Refactor to use `TerminalUI.display_warning()` and `TerminalUI.display_error()` respectively, which will in turn use `message_panel.py`.
*   **Redesign Final Output:** The final output sequence will be redesigned to be more concise and professional. This will include:
    *   A clean "Validation Complete" message.
    *   A well-formatted ERC results table.
    *   A single, clean panel displaying the generated SKiDL code.
    *   A professional-looking "Generated Files" summary.


## 3. Implementation Roadmap

1.  **Phase 1: Core Refactoring**
    *   Refactor `cli.py` to delegate all UI rendering to `TerminalUI`.
    *   Create the new `input_box.py`, `code_panel.py`, and `message_panel.py` components.
2.  **Phase 2: Component Integration**
    *   Integrate the new components into the `TerminalUI` class.
    *   Rework the `tables.py` component for unified table display.
    *   Enhance the `Spinner` component for consistent usage.
3.  **Phase 3: Flow and Content Rework**
    *   Refactor the application flow to eliminate duplicate output.
    *   Redesign and implement the new final output sequence.
4.  **Phase 4: Testing and Refinement**
    *   Thoroughly test the new UI to ensure it is working as expected.
    *   Refine the UI based on testing feedback.

By following this plan, we can create a more professional, user-friendly, and consistent UI/UX for the Circuitron CLI, which will significantly improve the overall user experience.
