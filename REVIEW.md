# Review

## Prompt verbosity

The validation and correction prompts span several hundred lines, e.g. the validator instructions begin at line 408 and continue past line 868 of `prompts.py`. This overwhelming context causes instruction loss and confusing tool usage.

## Correction input lacks design info

`format_code_correction_input()` only includes script text, validation summary, and optional ERC output, with no plan or part details.

## Loop intermixes validation and ERC

The pipeline repeatedly calls `run_code_correction()` whenever validation fails or ERC fails, without distinguishing the two phases.

- Overly complex knowledge-graph examples lead to incorrect queries and token overload.
- The corrector never receives design rationale, component info, or documentation.
- ERC is run automatically after validation but the corrector doesn’t directly invoke the ERC tool, causing confusion.
- The loop lacks progress tracking and can oscillate endlessly.

---

## Brainstorming

### Prompt Simplification

- Trim both validation and correction prompts to ~150–200 lines each.
- Provide a short “knowledge graph usage guide” and instruct agents to call a helper tool for further examples when unsure.
- Move long query examples and advanced patterns to documentation that agents can retrieve via `get_kg_usage_guide()`.

### Context-Rich Correction Inputs

Update formatting utilities so the correction agent receives:

- Summarized design plan (functional blocks, rationale, constraints).
- Selected components with pin mappings.
- Key documentation excerpts gathered during the docs step.

This ensures corrections preserve design intent.

### Custom Knowledge Graph Guide Tool

- Implement `get_kg_usage_guide(task_type: str)` (as proposed in `analysis.txt`) returning short query snippets for class, method, function, or import validation.
- Encourage agents to call it first before using `query_knowledge_graph`.

### Separated Validation and ERC Phases

- Modify the pipeline so the loop first resolves validation issues only.
- Once validation passes, run ERC via `run_erc_tool` explicitly and then correct any ERC problems.
- Track attempts separately for each phase and stop after N failed tries.

### Progress Tracking

- Introduce a `CorrectionContext` object storing previous issues, resolved items, and attempts. Provide this context to the correction agent each round so it focuses on unresolved problems.

### Documentation Gathering

- Ensure the documentation step happens before validation. If docs are missing, automatically invoke `perform_rag_query` on relevant topics before starting validation.

### ERC Issue Resolver Agent (optional enhancement)

- If ERC failures persist, consider a lightweight ERC-resolver agent specialized in applying SKiDL ERC fixes using documentation, separate from the main correction agent.

---

## Implementation Plan

### Create helper tool

- **File:** `circuitron/tools.py`
- Add `get_kg_usage_guide()` returning concise examples per `analysis.txt`.
- Export the tool in `__all__` and register it in `create_code_validation_agent()` and `create_code_correction_agent()`.

### Refactor prompts

- **File:** `circuitron/prompts.py`
- Rewrite `CODE_VALIDATION_PROMPT` and `CODE_CORRECTION_PROMPT` to follow the streamlined structure (see “Solution 2” in `analysis.txt`). Remove bulky query lists and point agents to `get_kg_usage_guide()` for advanced usage.
- Keep overall style consistent with other prompts but cap each to ~200 lines.

### Expand correction input

- **File:** `circuitron/utils.py`
- Extend `format_code_correction_input()` to accept optional plan, selection, and docs arguments.
- Format short summaries using helper functions (`format_plan_summary`, `format_selection_summary`) so the agent sees design intent and component data.

### Update pipeline workflow

- **File:** `circuitron/pipeline.py`
- Replace the current while-loop (lines 220‑260) with the two-phase “enhanced_validation_correction_cycle” described in `analysis.txt`.
- Call `run_code_correction_validation_only()` when validation fails; once validation passes, run ERC via `run_erc_tool` and if needed call `run_code_correction_erc_only()`.
- Pass the new plan/selection/docs context into correction calls.

### Implement correction-context tracking

- **Files:** new `circuitron/correction_context.py`, modify `pipeline.py`
- Define `CorrectionContext` (see `analysis.txt` lines 240‑259) to record issues and successful fixes.
- Provide `CorrectionContext.get_context_for_next_attempt()` output to `format_code_correction_input()`.

### Unit tests

- Update existing tests in `tests/test_pipeline.py` to cover the separated validation/ERC loops.
- Add tests for `get_kg_usage_guide()` and new formatting logic in `tests/test_utils_extra.py`.

### Documentation

- Document the redesigned workflow in `README.md` and `overview.md`.
- Add usage notes for `get_kg_usage_guide()` and the new context objects.

### Optional ERC resolver agent

- If ERC handling becomes complex, create `create_erc_resolver_agent()` in `agents.py` and invoke it in the second phase instead of `code_corrector`.

---

Implementing these steps will make prompts shorter, provide richer context to the correction agent, clarify tool usage, and separate validation from ERC handling for a more deterministic workflow.
