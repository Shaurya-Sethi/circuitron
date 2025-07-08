# Circuitron Validation & Correction Workflow Redesign - Implementation Plan

## Overview
This plan addresses critical issues in the Circuitron codebase related to prompt complexity, context loss, tool usage confusion, and inefficient validation/correction loops. The goal is to create a more streamlined, context-aware, and robust validation workflow.

## Task 1: Implement Knowledge Graph Usage Guide Tool
**Objective**: Create a helper tool that provides concise knowledge graph query examples to reduce prompt verbosity and improve tool usage.

**Implementation Details**:
- Create `get_kg_usage_guide(task_type: str)` function in `circuitron/tools.py`
- Support task types: "class", "method", "function", "import", "attribute", "examples"
- Return focused, actionable query examples for each task type
- Export the tool in `__all__` and register it in validation/correction agents
- Add comprehensive docstring with usage examples

**Files to Modify**:
- `circuitron/tools.py` - Add the new function and export
- `circuitron/agents.py` - Register tool in `create_code_validation_agent()` and `create_code_correction_agent()`

**Success Criteria**:
- Tool returns appropriate query examples for each task type
- Agents can call the tool to get targeted knowledge graph usage guidance
- Reduces need for extensive examples in prompts

## Task 2: Streamline Validation and Correction Prompts
**Objective**: Dramatically reduce prompt verbosity from 400+ lines to ~150-200 lines each while maintaining effectiveness.

**Implementation Details**:
- Rewrite `CODE_VALIDATION_PROMPT` in `circuitron/prompts.py`:
  - Remove extensive query examples (lines 450-800)
  - Replace with references to `get_kg_usage_guide()` tool
  - Keep essential validation logic and phase structure
  - Maintain systematic validation process but make it more concise
- Rewrite `CODE_CORRECTION_PROMPT` similarly:
  - Focus on correction strategy rather than extensive examples
  - Reference the knowledge graph guide tool for query help
  - Emphasize iterative improvement and context preservation

**Files to Modify**:
- `circuitron/prompts.py` - Major rewrite of both prompts

**Success Criteria**:
- Each prompt is 150-200 lines maximum
- Prompts maintain logical flow and essential instructions
- Agents are directed to use the knowledge graph guide tool when needed
- Validation and correction effectiveness is preserved or improved

## Task 3: Enhance Correction Input Context
**Objective**: Provide richer context to the correction agent including design plans, component selections, and documentation.

**Implementation Details**:
- Extend `format_code_correction_input()` in `circuitron/utils.py`:
  - Add optional parameters: `plan`, `selection`, `docs`
  - Create helper functions: `format_plan_summary()`, `format_selection_summary()`, `format_docs_summary()`
  - Include design rationale, component details, and key documentation excerpts
  - Maintain backward compatibility with existing calls
- Update pipeline calls to pass additional context
- Ensure correction agent receives comprehensive context about design intent

**Files to Modify**:
- `circuitron/utils.py` - Extend `format_code_correction_input()` and add helper functions
- `circuitron/pipeline.py` - Update calls to pass plan, selection, and docs context

**Success Criteria**:
- Correction agent receives design context, component information, and documentation
- Function maintains backward compatibility
- Corrections preserve design intent more effectively

## Task 4: Implement Correction Context Tracking
**Objective**: Create a system to track correction attempts, previous issues, and resolved problems to prevent infinite loops and improve correction efficiency.

**Implementation Details**:
- Create new file `circuitron/correction_context.py`:
  - Define `CorrectionContext` class to track:
    - Previous validation/ERC issues
    - Resolved problems
    - Attempt counts for different issue types
    - Success/failure patterns
  - Implement `get_context_for_next_attempt()` method
  - Add progress tracking and loop prevention logic
- Integrate with correction input formatting
- Provide historical context to correction agent

**Files to Modify**:
- `circuitron/correction_context.py` - New file with context tracking
- `circuitron/utils.py` - Integrate context tracking with input formatting
- `circuitron/pipeline.py` - Use context tracking in correction loops

**Success Criteria**:
- Correction attempts are tracked and limited
- Agents receive context about previous correction attempts
- Infinite loops are prevented through intelligent attempt limiting
- Progress is maintained across correction iterations

## Task 5: Separate Validation and ERC Phases
**Objective**: Redesign the pipeline to handle validation and ERC failures as distinct phases with separate correction strategies.

**Implementation Details**:
- Replace unified correction loop in `circuitron/pipeline.py` (lines 220-260):
  - Phase 1: Resolve validation issues only (ignore ERC)
  - Phase 2: Once validation passes, run ERC and fix electrical issues
  - Separate attempt counters for each phase
  - Different correction strategies for each phase
- Create specialized correction functions:
  - `run_code_correction_validation_only()` - focus on API/syntax issues
  - `run_code_correction_erc_only()` - focus on electrical rule violations
- Update agent prompts to handle phase-specific corrections
- Explicitly call `run_erc_tool` in Phase 2 rather than automatic execution

**Files to Modify**:
- `circuitron/pipeline.py` - Major redesign of validation/correction loop
- `circuitron/agents.py` - Potentially create specialized correction agents
- `circuitron/utils.py` - Add phase-specific correction input formatting

**Success Criteria**:
- Validation issues are resolved before ERC checking
- ERC issues are handled separately with appropriate electrical context
- Clear phase separation prevents confusion between API and electrical problems
- Each phase has appropriate attempt limits and progress tracking

## Task 6: Comprehensive Testing and Documentation
**Objective**: Ensure all changes are thoroughly tested and documented for maintainability and reliability.

**Implementation Details**:
- Update unit tests in `tests/test_pipeline.py`:
  - Test separated validation/ERC phases
  - Test correction context tracking
  - Test phase-specific correction loops
- Add tests in `tests/test_utils_extra.py`:
  - Test enhanced `format_code_correction_input()` with new parameters
  - Test helper formatting functions
  - Test `get_kg_usage_guide()` tool
- Create tests for new `correction_context.py` module
- Update documentation:
  - `README.md` - Document new workflow phases
  - `overview.md` - Explain separated validation/ERC approach
  - Add inline documentation for new functions and classes

**Files to Modify**:
- `tests/test_pipeline.py` - Updated pipeline tests
- `tests/test_utils_extra.py` - New utility function tests
- `tests/test_correction_context.py` - New file for context tracking tests
- `README.md` - Updated workflow documentation
- `overview.md` - Updated system overview

**Success Criteria**:
- All new functionality is covered by comprehensive tests
- Existing tests pass with modifications
- Documentation clearly explains the new workflow
- Code is maintainable and well-documented

## Implementation Order and Dependencies

1. **Task 1** (KG Guide Tool) - Foundation for prompt simplification
2. **Task 2** (Prompt Streamlining) - Depends on Task 1
3. **Task 3** (Enhanced Context) - Can be done in parallel with Task 2
4. **Task 4** (Context Tracking) - Can be done in parallel with Tasks 2-3
5. **Task 5** (Phase Separation) - Depends on Tasks 1-4
6. **Task 6** (Testing & Documentation) - Final integration and validation

## Expected Outcomes

- **Reduced Prompt Complexity**: Prompts reduced from 400+ lines to ~200 lines
- **Improved Context**: Correction agents receive comprehensive design context
- **Better Tool Usage**: Clear guidance reduces knowledge graph query confusion
- **Efficient Loops**: Separated phases prevent validation/ERC confusion
- **Robust Tracking**: Context tracking prevents infinite loops and improves success rates
- **Maintainable Code**: Clear separation of concerns and comprehensive testing

## Risk Mitigation

- **Backward Compatibility**: All changes maintain existing interfaces where possible
- **Incremental Testing**: Each task includes comprehensive testing before moving to next
- **Rollback Plan**: Git commits allow easy rollback of individual changes
- **Performance**: New context tracking designed to be lightweight and efficient

This plan addresses all critical issues identified in the review while maintaining system reliability and improving overall workflow efficiency.
