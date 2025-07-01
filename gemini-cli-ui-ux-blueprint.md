# Gemini CLI UI/UX Blueprint

## 1. Introduction

This document describes the user interface and interaction model implemented by Gemini CLI. It aggregates details from the TypeScript source code so that the same experience can be reproduced in any other command line project.

## 2. Codebase Structure Overview

- **packages/cli/src/ui** – React/Ink components, themes and hooks driving the TUI.
- **components/** – visual elements such as the header banner, input prompt, dialogs, message displays and status indicators.
- **themes/** – palette definitions and the `themeManager` controlling active theme selection.
- **contexts/** – React context providers for streaming state, overflow tracking and session statistics.
- **hooks/** – stateful logic for command processing, loading indicators, terminal size and more.

UI rendering starts from `App.tsx` which composes the major components and manages keyboard shortcuts.

## 3. UI/UX Feature Inventory

### 3.1 Startup Banner
- Uses ASCII art from `AsciiArt.ts` with color gradients applied through the active theme.
- Automatically chooses a short or long logo depending on terminal width.

### 3.2 Theming System
- Themes are objects describing foreground/background colors and accent hues. Example palette:
```ts
export const darkTheme: ColorsTheme = {
  type: 'dark',
  Background: '#1E1E2E',
  Foreground: '#CDD6F4',
  LightBlue: '#ADD8E6',
  AccentBlue: '#89B4FA',
  AccentPurple: '#CBA6F7',
  AccentCyan: '#89DCEB',
  AccentGreen: '#A6E3A1',
  AccentYellow: '#F9E2AF',
  AccentRed: '#F38BA8',
  Comment: '#6C7086',
  Gray: '#6C7086',
  GradientColors: ['#4796E4', '#847ACE', '#C3677F'],
};
```
- `themeManager` maintains a list of available themes and exposes `setActiveTheme()`.
- Users can switch themes via the `/theme` command which opens `ThemeDialog` for selection.

### 3.3 Prompt & Input Handling
- `InputPrompt` renders the command line box and manages history navigation, auto-completion and shell mode.
- Key bindings include:
```ts
// Ctrl+A / Ctrl+E move to start/end
if (key.ctrl && input === 'a') { buffer.move('home'); }
if (key.ctrl && input === 'e') { buffer.move('end'); }
// Ctrl+L clears the screen
if (key.ctrl && input === 'l') { onClearScreen(); }
// Ctrl+P / Ctrl+N traverse input history
if (key.ctrl && input === 'p') { inputHistory.navigateUp(); }
if (key.ctrl && input === 'n') { inputHistory.navigateDown(); }
```
- Enter submits unless the user presses Ctrl+Enter (adds newline). Escape cancels suggestions or exits shell mode.
- When shell mode is toggled by typing `!`, submitted text is executed via the system shell.
- Autocomplete suggestions appear below the prompt using `SuggestionsDisplay` with a scrollable list.

### 3.4 Output Formatting & Display
- User and Gemini messages are wrapped with prefixes (`>`, `✦`, etc.) and colored accents.
- Markdown text is parsed in `MarkdownDisplay` which handles inline formatting, code fences and lists. Code blocks are syntax highlighted with `lowlight` via `colorizeCode()`.
- Diff outputs and tool results are shown using `DiffRenderer` and `ToolMessage`, supporting large outputs with overflow management through `MaxSizedBox`.

### 3.5 Status Indicators & Dynamic Feedback
- `LoadingIndicator` shows a spinner and elapsed time while waiting for Gemini with phrases cycled by `usePhraseCycler`.
- `AutoAcceptIndicator` and `ShellModeIndicator` communicate special states (auto-edit mode, shell mode) in the footer area.
- Session statistics such as token counts are presented in `StatsDisplay`.

### 3.6 Command Menus & Navigation
- Commands starting with `/` open dialogs or perform actions (`/theme`, `/auth`, `/editor`, `/help`, etc.).
- Dialog components (`ThemeDialog`, `AuthDialog`, `EditorSettingsDialog`) render selectable lists with keyboard navigation.
- A help overlay (`Help`) lists available commands and shortcuts.

## 4. Design Principles & Style Guide

- **Look & Feel:** Retro terminal aesthetic with optional color gradients.
- **Color Palette:** Determined by the current theme; supports both light and dark variants and an ANSI fallback.
- **Layout:** Content width is limited (~90% of terminal width). Boxes use rounded or single borders for separation.
- **Typography:** Bold and italic text for emphasis, strikethrough for deletions. Prefix symbols (`✦`, `ℹ`, `✕`) denote message types.
- **Spacing:** Components use small margins/padding (typically 1 character) to keep output compact.

## 5. Key Code Snippets & Patterns

### Theme Manager
```ts
class ThemeManager {
  private activeTheme: Theme = DEFAULT_THEME;
  setActiveTheme(name?: string) {
    const found = this.findThemeByName(name);
    if (found) { this.activeTheme = found; return true; }
    return false;
  }
  getActiveTheme(): Theme {
    if (process.env.NO_COLOR) return NoColorTheme;
    return this.activeTheme;
  }
}
```
This singleton allows the rest of the UI to read colors via getters from `Colors`, providing theme-aware values.

### Input Prompt Rendering
```tsx
<Box borderStyle="round" borderColor={shellModeActive ? Colors.AccentYellow : Colors.AccentBlue} paddingX={1}>
  <Text color={shellModeActive ? Colors.AccentYellow : Colors.AccentPurple}>
    {shellModeActive ? '! ' : '> '}
  </Text>
  <Box flexGrow={1} flexDirection="column">
    {/* lines of editable text or placeholder */}
  </Box>
</Box>
```
The prompt shows a leading `!` when in shell mode and otherwise `>`. It highlights the character at the cursor using inverse coloring.

### Gemini Responding Spinner
```tsx
export const GeminiRespondingSpinner: React.FC = ({ nonRespondingDisplay }) => {
  const state = useStreamingContext();
  if (state === StreamingState.Responding) return <Spinner type="dots" />;
  if (nonRespondingDisplay) return <Text>{nonRespondingDisplay}</Text>;
  return null;
};
```
Switches between an animated spinner during streaming and optional placeholder text otherwise.

### Tool Group Message Layout
```tsx
<Box flexDirection="column" borderStyle="round" width="100%" marginLeft={1}>
  {toolCalls.map(tool => (
    <Box key={tool.callId} flexDirection="column" minHeight={1}>
      <ToolMessage {...tool} />
      {tool.status === ToolCallStatus.Confirming && <ToolConfirmationMessage ... />}
    </Box>
  ))}
</Box>
```
Tool calls are grouped inside a bordered box. Each entry displays status icons, tool name and optional results.

## 6. Step-by-Step Reproduction Guide

1. **Project Layout**
   - Create a `ui` directory with subfolders: `components`, `themes`, `contexts`, and `hooks`.
   - Implement a root `App` component to assemble the header, history list, input prompt and footer.

2. **Rendering the Banner**
   - Embed ASCII art as constants (see appendix) and print it on startup using gradient colors from the active theme.

3. **Theme Support**
   - Define `Theme` objects as shown above and a `themeManager` singleton.
   - Provide a `/theme` command that opens a selection dialog allowing the user to preview and apply themes. Persist the choice in configuration files.

4. **Prompt Handling**
   - Implement a buffer-based text editor with cursor movement and history navigation.
   - Map key bindings (Ctrl+A/E/L/P/N, Escape, Enter, Ctrl+Enter) similar to the snippet in section 5.
   - Integrate completion suggestions triggered by `@` or `/` prefixes and display them below the prompt.

5. **Output Display**
   - Use message components with clear prefixes for user, Gemini and system messages.
   - Parse markdown into styled text and highlight code using a syntax highlighter equivalent to `lowlight`.
   - Wrap large outputs in size-constrained containers to prevent terminal flicker.

6. **Dynamic Feedback**
   - Maintain a streaming state context to show spinners and update elapsed time.
   - Provide notifications such as update messages or auto-accept status in the footer area.

7. **Accessibility and Responsiveness**
   - Recalculate terminal size on resize events to adjust layout.
   - Offer a no-color mode via an environment variable to ensure output works in colorless terminals.

## 7. Customization & Extensibility Notes

- **Decoupling from Gemini** – Replace calls to the Gemini client with your own backend while keeping the same event structure.
- **Extending Themes** – Add new themes by creating additional `Theme` objects and registering them with `themeManager`.
- **Modifying Banners** – Edit the ASCII art constants or provide user configuration for custom logos.
- **Adding Commands** – Follow the pattern in `slashCommandProcessor` to define new `/` commands with actions.

## 8. Asset & Configuration Appendix

### ASCII Art Logos
```
<shortAsciiLogo>
   █████████  ██████████ ██████   ██████ █████ ██████   █████ █████
  ███░░░░░███░░███░░░░░█░░██████ ██████ ░░███ ░░██████ ░███ ░░███
 ███     ░░░  ░███  █ ░  ░███░█████░███  ░███  ░███░███ ░███  ░███
░███          ░██████    ░███░░███ ░███  ░███  ░███░░███░███  ░███
░███    █████ ░███░░█    ░███ ░░░  ░███  ░███  ░███ ░░██████  ░███
░░███  ░░███  ░███ ░   █ ░███      ░███  ░███  ░███  ░░█████  ░███
 ░░█████████  ██████████ █████     █████ █████ █████  ░░█████ █████
  ░░░░░░░░░  ░░░░░░░░░░ ░░░░░     ░░░░░ ░░░░░ ░░░░░    ░░░░░ ░░░░░
```
```
<longAsciiLogo>
 ███            █████████  ██████████ ██████   ██████ █████ ██████   █████ █████
░░░███         ███░░░░░███░░███░░░░░█░░██████ ██████ ░░███ ░░██████ ░███ ░░███
  ░░░███      ███     ░░░  ░███  █ ░  ░███░█████░███  ░███  ░███░███ ░███  ░███
    ░░░███   ░███          ░██████    ░███░░███ ░███  ░███  ░███░░███░███  ░███
     ███░    ░███    █████ ░███░░█    ░███ ░░░  ░███  ░███  ░███ ░░██████  ░███
   ███░      ░░███  ░░███  ░███ ░   █ ░███      ░███  ░███  ░███  ░░█████  ░███
 ███░         ░░█████████  ██████████ █████     █████ █████ █████  ░░█████ █████
░░░            ░░░░░░░░░  ░░░░░░░░░░ ░░░░░     ░░░░░ ░░░░░ ░░░░░    ░░░░░ ░░░░░
```
These logos are displayed with gradient coloring when supported.

### UI Width Constants
```ts
const EstimatedArtWidth = 59;
const BOX_PADDING_X = 1;
export const UI_WIDTH = EstimatedArtWidth + BOX_PADDING_X * 2 + 2; // ~63 columns
```
This determines the width of the banner box so that it fits the ASCII art.
