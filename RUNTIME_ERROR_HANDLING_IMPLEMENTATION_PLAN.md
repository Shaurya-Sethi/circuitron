# Runtime Error Handling Implementation Plan

## Executive Summary

After analyzing the current Circuitron codebase, I've identified a critical gap in error handling: **runtime errors that occur during script execution are not handled by the correction pipeline**. The current system only invokes correction agents when validation fails or ERC reports warnings/errors, but Python runtime errors (import failures, syntax errors, API misuse that passes validation, etc.) cause the entire pipeline to fail.

## Current System Analysis

### Current Pipeline Flow
1. **Code Generation** → Generates SKiDL code
2. **Code Validation** → Validates syntax/API usage (static analysis)  
3. **Code Correction** → Fixes validation issues (if any)
4. **ERC Execution** → Runs script to perform electrical rule checks
5. **ERC Handling** → Fixes electrical issues (if any)

### Critical Gap Identified
The current system fails when:
- Script has runtime errors (import failures, runtime API misuse)
- ERC execution fails with Python exceptions instead of ERC warnings/errors
- The script executes but crashes before reaching `ERC()` call

### Current Architecture Strengths
- Well-structured correction context management
- Proper separation of concerns between agents
- Good retry logic with loop protection
- Comprehensive ERC handling for electrical issues

### Current Architecture Weaknesses
- No runtime error detection/correction capability
- ERC agent only invoked for ERC-specific issues, not runtime failures
- Pipeline fails hard on runtime errors instead of attempting correction

## Recommended Solution: Runtime Error Correction Agent

### Implementation Strategy
I recommend implementing a **new Runtime Error Correction Agent** that sits between validation/correction and ERC handling. This agent would:

1. **Execute the script in a controlled environment** (same Docker setup as ERC)
2. **Capture runtime errors** before they reach ERC
3. **Provide comprehensive error context** to a specialized correction agent
4. **Update the correction context** with runtime error attempts
5. **Retry until runtime errors are resolved** or max attempts reached

### Architecture Changes Required

#### 1. New Agent: Runtime Error Corrector
```python
# New agent in agents.py
runtime_error_corrector = create_runtime_error_correction_agent()

# New model in models.py
class RuntimeErrorCorrectionOutput(BaseModel):
    runtime_issues_identified: List[str]
    corrections_applied: List[str] 
    execution_status: Literal["success", "runtime_error", "timeout"]
    error_details: str
    corrected_code: str
    execution_output: str
```

#### 2. Enhanced Pipeline Flow
```
Code Generation → Code Validation → Code Correction → 
**Runtime Error Check** → Runtime Error Correction (if needed) → 
ERC Execution → ERC Handling
```

#### 3. New Runtime Execution Function
```python
async def run_runtime_check(
    code_output: CodeGenerationOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
) -> tuple[bool, dict[str, object] | None]:
    """Execute script to check for runtime errors before ERC.
    
    Returns:
        (success: bool, error_info: dict | None)
    """
```

#### 4. Enhanced Correction Context
```python
# Add to CorrectionContext
runtime_attempts: int = 0
runtime_issues_history: List[Dict[str, Any]] = field(default_factory=list)

def add_runtime_attempt(self, error_info: Dict[str, Any], corrections: List[str]) -> None:
    """Record a runtime error correction attempt."""
    
def should_continue_runtime_attempts(self) -> bool:
    """Decide whether to continue runtime correction attempts."""
```

## Detailed Implementation Plan

### Phase 1: Core Infrastructure (2-3 hours)

#### 1.1 Create Runtime Error Correction Model
**File:** `circuitron/models.py`
```python
class RuntimeErrorCorrectionOutput(BaseModel):
    """Output from the Runtime Error Correction Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    runtime_issues_identified: List[str] = Field(
        default_factory=list,
        description="Python runtime errors found with detailed descriptions and locations"
    )
    corrections_applied: List[str] = Field(
        default_factory=list,
        description="Runtime error corrections made with technical rationale"
    )
    execution_status: Literal["success", "runtime_error", "timeout"] = Field(
        description="Final execution status after corrections"
    )
    error_details: str = Field(
        description="Complete error traceback and diagnostic information"
    )
    corrected_code: str = Field(
        description="Updated SKiDL code with runtime issues resolved"
    )
    execution_output: str = Field(
        description="Captured stdout/stderr from script execution attempt"
    )
```

#### 1.2 Create Runtime Execution Function
**File:** `circuitron/tools.py`
```python
async def run_runtime_check(script_path: str) -> str:
    """Execute a SKiDL script and capture runtime errors.
    
    Similar to run_erc but stops before ERC() call to isolate runtime issues.
    Returns JSON with success flag, error details, and execution output.
    """
    wrapper = textwrap.dedent("""
        import os
        import json, runpy, io, contextlib, traceback
        from skidl import *
        
        # Set up KiCad environment
        os.environ['KICAD5_SYMBOL_DIR'] = '/usr/share/kicad/library'
        set_default_tool(KICAD5)
        
        out = io.StringIO()
        err = io.StringIO()
        success = True
        error_details = ""
        
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                # Execute script but don't call ERC() yet
                script_globals = runpy.run_path('/tmp/script.py', run_name='__main__')
                
                # Validate that basic SKiDL structures exist
                if 'default_circuit' in dir():
                    print("Circuit object created successfully")
                else:
                    print("Warning: No default circuit found")
                    
        except Exception as exc:
            success = False
            error_details = traceback.format_exc()
            err.write(str(exc))
            
        result = {
            'success': success,
            'error_details': error_details,
            'stdout': out.getvalue(),
            'stderr': err.getvalue()
        }
        print(json.dumps(result))
    """)
    
    # Implementation follows same pattern as run_erc
    # ...
```

#### 1.3 Enhance Correction Context
**File:** `circuitron/correction_context.py`
```python
@dataclass
class CorrectionContext:
    # ... existing fields ...
    runtime_attempts: int = 0
    runtime_issues_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_runtime_attempt(
        self, error_info: Dict[str, Any], corrections: List[str]
    ) -> None:
        """Record a runtime error correction attempt."""
        self.runtime_attempts += 1
        self.runtime_issues_history.append({
            "attempt": self.runtime_attempts,
            "error_info": error_info,
            "corrections": corrections,
        })
        
    def should_continue_runtime_attempts(self) -> bool:
        """Decide whether to continue runtime correction attempts."""
        if self.runtime_attempts >= self.max_attempts:
            return False
        # Add logic to detect if same error persists
        return True
        
    def get_runtime_context_for_agent(self) -> str:
        """Return formatted context for runtime error correction."""
        # Implementation similar to get_context_for_next_attempt
        pass
```

### Phase 2: Agent Creation (2-3 hours)

#### 2.1 Create Runtime Error Correction Agent
**File:** `circuitron/agents.py`
```python
def create_runtime_error_correction_agent() -> Agent:
    """Create and configure the Runtime Error Correction Agent."""
    model_settings = ModelSettings(
        tool_choice=_tool_choice_for_mcp(settings.runtime_correction_model)
    )
    
    tools: list[Tool] = [get_kg_usage_guide, run_runtime_check_tool]
    
    return Agent(
        name="Circuitron-RuntimeCorrector",
        instructions=RUNTIME_ERROR_CORRECTION_PROMPT,
        model=settings.runtime_correction_model,
        output_type=RuntimeErrorCorrectionOutput,
        tools=tools,
        mcp_servers=[mcp_manager.get_server()],
        model_settings=model_settings,
    )

# Add to module exports
runtime_error_corrector = create_runtime_error_correction_agent()
```

#### 2.2 Create Runtime Error Correction Prompt
**File:** `circuitron/prompts.py`
```python
RUNTIME_ERROR_CORRECTION_PROMPT = f"""{RECOMMENDED_PROMPT_PREFIX}
You are Circuitron-RuntimeCorrector, a SKiDL runtime debugging specialist.

**Goal**: Resolve Python runtime errors that prevent SKiDL scripts from executing properly.

**Your Focus**: Runtime issues that occur during script execution:
- Import failures and missing dependencies
- Runtime API misuse not caught by validation
- Incorrect object instantiation or method calls
- Environment setup issues
- Reference errors and attribute access problems

**Available Tools**
- `run_runtime_check` – Execute the script and capture detailed runtime error information
- `query_knowledge_graph` – Query the SKiDL knowledge graph to verify correct API usage
- `perform_rag_query` – Search SKiDL documentation for runtime usage patterns
- `get_kg_usage_guide` – Get structured examples for knowledge graph queries

**Workflow**
1. Review the provided runtime error details and execution output
2. Use `run_runtime_check` to validate your fixes incrementally
3. Use documentation tools to confirm correct SKiDL runtime usage patterns
4. Apply targeted fixes for runtime errors
5. Re-test until the script executes without runtime errors
6. Do **not** address ERC issues - another agent handles electrical problems

**Success Criteria**
- Script executes without Python runtime errors
- Basic SKiDL objects are created successfully
- Script reaches the point where ERC() could be called

**Common Runtime Error Patterns**
- Missing imports: `from skidl import *` placement issues
- Incorrect Part instantiation: wrong library names, missing quotes
- Net connection syntax errors: `+=` vs `=` confusion
- Environment setup: KICAD library path issues
- Variable scope problems: objects not accessible where needed

Stop once runtime execution succeeds. The ERC phase will handle electrical issues separately.
"""
```

### Phase 3: Pipeline Integration (3-4 hours)

#### 3.1 Create Pipeline Helper Functions
**File:** `circuitron/pipeline.py`
```python
async def run_runtime_check_and_correction(
    code_output: CodeGenerationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext,
) -> tuple[CodeGenerationOutput, bool]:
    """Check for runtime errors and correct them if needed.
    
    Returns:
        (updated_code_output, runtime_success)
    """
    # Create script with runtime check wrapper
    runtime_check_script = prepare_runtime_check_script(code_output.complete_skidl_code)
    script_path = write_temp_skidl_script(runtime_check_script)
    
    try:
        # Execute runtime check
        runtime_result_json = await run_runtime_check(script_path)
        runtime_result = json.loads(runtime_result_json)
        
        if runtime_result.get("success", False):
            return code_output, True
            
        # Runtime error detected - invoke correction agent
        input_msg = format_runtime_correction_input(
            code_output.complete_skidl_code,
            runtime_result,
            plan,
            selection,
            docs,
            context,
        )
        
        result = await run_agent(runtime_error_corrector, sanitize_text(input_msg))
        correction = cast(RuntimeErrorCorrectionOutput, result.final_output)
        
        # Update code and context
        code_output.complete_skidl_code = correction.corrected_code
        context.add_runtime_attempt(runtime_result, correction.corrections_applied)
        
        return code_output, correction.execution_status == "success"
        
    finally:
        if script_path:
            try:
                os.remove(script_path)
            except OSError:
                pass
```

#### 3.2 Update Main Pipeline Function
**File:** `circuitron/pipeline.py`
```python
async def pipeline(prompt: str, show_reasoning: bool = False, output_dir: str | None = None) -> CodeGenerationOutput:
    # ... existing code until validation correction loop ...
    
    # NEW: Runtime error check and correction phase
    if validation.status == "pass":
        runtime_success = False
        runtime_loop_count = 0
        
        while not runtime_success and correction_context.should_continue_runtime_attempts():
            runtime_loop_count += 1
            if runtime_loop_count > 5:  # Lower limit for runtime errors
                raise PipelineError("Runtime error correction loop exceeded maximum iterations")
                
            code_out, runtime_success = await run_runtime_check_and_correction(
                code_out, plan, selection, docs, correction_context
            )
            
        if not runtime_success:
            if settings.dev_mode:
                pretty_print_generated_code(code_out)
            raise PipelineError("Runtime errors persist after maximum correction attempts")
    
    # Continue with existing ERC handling...
    erc_result = None
    if validation.status == "pass":
        # ... existing ERC code ...
```

#### 3.3 Create Utility Functions
**File:** `circuitron/utils.py`
```python
def prepare_runtime_check_script(full_script: str) -> str:
    """Return a modified script that stops before ERC() for runtime checking."""
    # Similar to prepare_erc_only_script but removes ERC() call entirely
    new_lines = []
    for line in full_script.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            new_lines.append(line)
            continue
        # Comment out both generate_* and ERC() calls
        if re.search(r"\b(generate_\w+|ERC)\s*\(", stripped):
            new_lines.append(f"# {line}")
        else:
            new_lines.append(line)
    return "\n".join(new_lines)

def format_runtime_correction_input(
    code: str,
    runtime_result: dict,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext | None = None,
) -> str:
    """Format input for the runtime error correction agent."""
    # Implementation follows pattern of other format_*_input functions
    pass
```

### Phase 4: Configuration and Testing (2-3 hours)

#### 4.1 Update Configuration
**File:** `circuitron/config.py`
```python
# Add runtime correction model setting
runtime_correction_model: str = Field(
    default="gpt-4o-mini",
    description="Model for runtime error correction agent"
)
```

#### 4.2 Update Exports
**File:** `circuitron/pipeline.py`
```python
__all__ = [
    # ... existing exports ...
    "run_runtime_check_and_correction",
    "RuntimeErrorCorrectionOutput",
]
```

## Implementation Benefits

### 1. **Robust Error Handling**
- Catches runtime errors before they crash the pipeline
- Provides detailed error context for effective correction
- Maintains separation between runtime and electrical issues

### 2. **Maintains Current Architecture**
- Builds on existing correction context system
- Follows established agent patterns and conventions
- Preserves current pipeline flow with minimal disruption

### 3. **Comprehensive Coverage**
- Validates actual script execution, not just static analysis
- Catches environment-specific issues (Docker, library paths)
- Handles complex runtime scenarios validation might miss

### 4. **Intelligent Retry Logic**
- Reuses proven correction context management
- Prevents infinite loops with proper attempt tracking
- Learns from previous failed correction attempts

## Alternative Approaches Considered

### Option A: Extend Code Corrector Agent
**Pros:** No new agent needed, simpler architecture
**Cons:** Mixes runtime and validation concerns, harder to manage different error types

### Option B: Enhanced ERC Agent
**Pros:** Reuses existing ERC infrastructure
**Cons:** Confuses electrical and runtime issues, ERC agent already complex

### Option C: New Runtime Error Agent (Recommended)
**Pros:** Clear separation of concerns, specialized handling, maintains architecture
**Cons:** Adds complexity, requires new agent development

## Risk Assessment

### Low Risk
- Uses existing Docker execution patterns
- Follows established agent creation patterns
- Builds on proven correction context system

### Medium Risk
- Increases pipeline complexity
- Adds new execution phase that could introduce delays
- Requires careful error categorization

### Mitigation Strategies
- Implement comprehensive logging for runtime correction attempts
- Add circuit breakers to prevent infinite runtime correction loops
- Use separate timeout values for runtime vs ERC phases
- Implement fallback mechanisms for runtime correction failures

## Success Metrics

### Functional Success
- [ ] Pipeline handles runtime errors without crashing
- [ ] Runtime errors are correctly identified and fixed
- [ ] ERC phase receives working code for electrical validation
- [ ] No infinite loops in runtime correction

### Performance Success
- [ ] Runtime correction completes within reasonable time (< 2 minutes)
- [ ] Success rate improvement in end-to-end pipeline execution
- [ ] Reduced pipeline failure rate due to runtime errors

## Conclusion

The **Runtime Error Correction Agent** approach provides the most robust and maintainable solution to the identified gap. It preserves the current architecture while adding comprehensive runtime error handling that will significantly improve pipeline reliability. The implementation follows established patterns and can be developed incrementally with minimal risk to existing functionality.

The estimated implementation time is **10-12 hours** total, which can be split across the four phases for manageable development cycles.
