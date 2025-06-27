# AGENTS.md

## Purpose

This file exists to optimize the performance of OpenAI Codex and other AI agents working on this repository.
It defines **project-specific context, architecture, coding conventions, and process requirements** to ensure generated code is high-quality, consistent, and production-ready.

---

## 1. Project Overview & Structure

> **For all context regarding project purpose, architecture, features, tech stack, workflow, and roadmap, always reference the full and latest `overview.md` file located at the repository root.**
>
> * **If you require project context, read and parse `overview.md` directly.**
> * **If in doubt about design intent, feature scope, or workflow, consult `overview.md` before proceeding.**

---

## 2. External Documentation – Always Consult Before Generating Code

OpenAI Codex (and all AI agents) **must consult the following official docs before modifying any file** in this project:

* **OpenAI Agents SDK reference**
  URL: [https://openai.github.io/openai-agents-python/](https://openai.github.io/openai-agents-python/)
  GitHub: [`openai/openai-agents-python`](https://github.com/openai/openai-agents-python)
  **Offline Fallback:** If unable to access the official documentation, consult the local file `openai_agents_sdk_docs_final_perfect.md` in the project root, which contains the complete, LLM-optimized OpenAI Agents SDK documentation.

* **OpenAI Platform API reference**
  URL: [https://platform.openai.com/docs/guides/](https://platform.openai.com/docs/guides/)

* **SKiDL reference**
  URL: [https://devbisme.github.io/skidl/](https://devbisme.github.io/skidl/)

> **When generating code or reasoning, always cite relevant sections from these docs inline in comments where appropriate.**
>
> *If uncertain about any API, pattern, or tool behavior, re-query the official docs and/or ask the user for clarification—**never hallucinate code**! If official documentation is inaccessible, use the local offline documentation files provided in the project root.*

---

## 3. Coding Style & Conventions

* **Language:** Python 3.11+

* **Linting:** [`ruff`](https://docs.astral.sh/ruff/) (`pyproject.toml` included)

* **Type Checking:** [`mypy --strict`](https://mypy.readthedocs.io/en/stable/)

* **Naming Conventions:**

  * Function and variable names: `snake_case`
  * Class names: `PascalCase`

* **Docstrings:**
  All public functions/classes require complete docstrings:

  * List all arguments and their types
  * Specify the return type
  * Provide a concise usage example

* **Agents-SDK Tools:**
  Each tool must be **pure**—no hidden side effects.

---

## 4. Testing Protocols

* **Unit Testing:**
  Every new Agents-SDK tool must have a unit test with **mocked LLM outputs**.
* **Examples:**
  Every design prompt in `/examples/` must “round-trip”: prompt → plan → SKiDL → `.sch` + `.kicad_pcb` in CI.
* **Coverage:**

  * Achieve and maintain **≥90% branch coverage** on backend utilities.
  * Add edge-case tests for every Agents-SDK tool and SKiDL helper.
* **Test Framework:**
  Use `pytest`.
* **Continuous Testing:**
  After every logical change, **run all tests quietly**:

  ```
  pytest -q
  ```

  Refuse to commit any code if tests fail or coverage decreases.

---

## 5. Pull Request (PR) Guidelines

* PRs must include:

  * Summary of changes
  * List of affected files
  * Rationale (if implementing design choices, link to relevant chain-of-thought or RAG evidence)
  * Confirmation that `pytest -q` passes and coverage is unchanged or increased
* PR messages must mention:

  * Any changes to Agents-SDK tools or core architecture
  * How external documentation (see Section 2) was referenced

---

## 6. Full-Code Ownership & Test-Driven Development (TDD) Mandate

> **Codex (and other AI agents) are the sole implementation agent for this repository.**
>
> * Treat the project as a green-field codebase:
>   Generate all source files, config, and docs needed to meet requirements.
> * Follow strict TDD:
>   \- Write a failing test (`pytest`) for any new behavior before writing production code.
>   \- Write minimal production code to pass the test.
>   \- Refactor for clarity after passing.
> * Keep coverage ≥90%; add edge/corner-case tests for every feature.

---

## 7. Common Patterns & Reminders

* **Always prefer explicit, readable code with clear error handling.**
* **Never use undocumented SKiDL or Agents-SDK features.**
* **All interaction with hardware or the file system must be idempotent and easily mockable in tests.**

---

## 8. Frequently Used References (for Codex)

* [SKiDL API reference](https://devbisme.github.io/skidl/)
* [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/)
* **Local Documentation:** `openai_agents_sdk_docs_final_perfect.md` - Complete offline OpenAI Agents SDK documentation (use when internet access is unavailable)

---

## 9. For OpenAI Codex and AI Agents

* If you are ever uncertain about project requirements, **ask the user for clarification rather than hallucinating.**
* Re-query the documentation links above regularly for changes or updates.

---

**End of AGENTS.md**

---
