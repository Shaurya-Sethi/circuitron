Title: Improve initial prompt: boxed input UI
Date: 2025-08-09

Summary
- Implemented a "nice input box" for the initial (and general) user prompts.
- The InputBox component now renders a three-line, Unicode-bordered prompt so the cursor appears inside a box.
- Kept graceful fallback to built-in input() for headless test environments.

Changes
- Updated circuitron/ui/components/input_box.py to compose a multi-line HTML prompt with accent-colored borders:
  ┌─ <question>
  │
  └─ ❯ [input]
- Left TerminalUI.prompt_user unchanged so all existing call sites automatically benefit.

Tests
- Extended tests/test_input_box.py with an additional test to verify the presence of border glyphs and message text in the HTML provided to PromptSession.prompt().
- Existing test asserting HTML usage and message presence still passes conceptually (environment not executed here).

Notes
- No API changes; this is a purely presentational improvement.
- Future work: consider dialog-based input for richer UX (prompt_toolkit dialogs) and add keyboard-driven command menus for `/` triggers (Issue 3).

