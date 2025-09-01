# Dependency Update Migration Guide

## Overview
This guide covers the migration from:
- `openai-agents` 0.1.0 → 0.2.10
- `skidl` 2.0.1 → 2.1.0

## Pre-Migration Checklist

### 1. Backup Current State
```bash
git checkout -b backup-before-upgrade
git push origin backup-before-upgrade
```

### 2. Document Current Functionality
- [ ] Run current test suite: `pytest -q tests/`
- [ ] Document any failing tests (unrelated to upgrade)
- [ ] Test basic CLI functionality if possible
- [ ] Note current behavior of key features

### 3. Environment Setup
```bash
# Activate virtual environment
& C:/Users/shaur/circuitron/circuitron_venv/Scripts/Activate.ps1

# Install updated dependencies
pip install -r requirements.txt

# Or install individual packages
pip install openai-agents==0.2.10
pip install skidl==2.1.0
```

## Migration Steps

### Step 1: Run Migration Tests
```bash
cd /home/runner/work/circuitron/circuitron
python /tmp/migration_test.py
```

This will test:
- Import compatibility
- Agent creation patterns
- Function tool decorators
- MCP server functionality
- SKiDL compatibility
- Circuitron agent functions
- Full test suite

### Step 2: Identify Breaking Changes

#### OpenAI Agents SDK Potential Issues
Based on API analysis, check for:

1. **Agent Constructor Changes**
   - Parameter names or types
   - Default values
   - Required vs optional parameters

2. **ModelSettings Changes**
   - Parameter structure
   - Default behavior
   - Tool choice options

3. **Function Tool Decorator**
   - Signature changes
   - Return type handling
   - Async/sync requirements

4. **MCP Server Integration**
   - Connection methods
   - Configuration options
   - Tool exposure patterns

#### SKiDL Potential Issues
1. **Import Changes**
   - Module structure
   - Class/function locations

2. **Configuration Changes**
   - Library paths
   - Tool defaults
   - Environment variables

### Step 3: Fix Common Breaking Changes

#### Agent Constructor Fixes
If agent creation fails, check these patterns:

```python
# Before (0.1.0)
agent = Agent(
    name="Test",
    instructions="...",
    model="gpt-4o",
    output_type=SomeType,
    tools=[tool1, tool2],
    model_settings=ModelSettings(tool_choice="required")
)

# After (0.2.10) - May need parameter changes
# Check if any parameters were renamed or removed
```

#### Function Tool Fixes
If `@function_tool` fails:

```python
# Before
from agents import function_tool

@function_tool
async def my_tool(param: str) -> str:
    return result

# After - Check if decorator parameters changed
# May need additional configuration
```

### Step 4: Update Circuitron Code

#### Files to Check for Changes
1. **`circuitron/agents.py`**
   - All `create_*_agent()` functions
   - Agent constructor calls
   - ModelSettings usage

2. **`circuitron/tools.py`**
   - `@function_tool` decorators
   - Tool function signatures
   - MCP server creation

3. **`circuitron/mcp_manager.py`**
   - MCPServer import and usage
   - Connection patterns

4. **`circuitron/utils.py`**
   - RunResult and ReasoningItem usage

5. **`circuitron/prompts.py`**
   - SKiDL imports and usage

6. **`circuitron/docker_session.py`**
   - SKiDL setup scripts

### Step 5: Test Critical Paths

#### Core Functionality Tests
```bash
# Test agent creation
python -c "from circuitron.agents import create_planning_agent; agent = create_planning_agent(); print('✓ Planning agent created')"

# Test tool creation
python -c "from circuitron.tools import execute_calculation; print('✓ Tools imported')"

# Test MCP manager
python -c "from circuitron.mcp_manager import mcp_manager; print('✓ MCP manager imported')"
```

#### Integration Tests
```bash
# Run specific test categories
pytest tests/test_agents.py -v
pytest tests/test_tools.py -v  
pytest tests/test_pipeline.py -v
```

### Step 6: Validate Full System

#### Run Complete Test Suite
```bash
pytest -q tests/
```

#### Manual Testing
If environment allows:
```bash
# Test CLI basics
python -m circuitron --help

# Test simple pipeline (if MCP server available)
# python -m circuitron "Create a simple LED circuit"
```

## Common Breaking Changes & Fixes

### Issue: Agent Creation Fails
**Symptoms:**
```
TypeError: Agent.__init__() got an unexpected keyword argument 'X'
```

**Fix:**
1. Check Agent class documentation in 0.2.10
2. Update parameter names
3. Remove deprecated parameters
4. Add new required parameters

### Issue: Function Tool Decorator Fails
**Symptoms:**
```
TypeError: function_tool() missing required argument
```

**Fix:**
1. Check if decorator now requires parameters
2. Update function signatures if needed
3. Ensure async/await patterns are correct

### Issue: MCP Server Connection Fails
**Symptoms:**
```
AttributeError: 'MCPServer' object has no attribute 'connect'
```

**Fix:**
1. Check updated MCP server API
2. Update connection methods
3. Check initialization parameters

### Issue: SKiDL Import Errors
**Symptoms:**
```
ImportError: cannot import name 'X' from 'skidl'
```

**Fix:**
1. Check SKiDL 2.1.0 API documentation
2. Update import statements
3. Check for renamed functions/classes

## Post-Migration Validation

### Checklist
- [ ] All tests pass
- [ ] No import errors
- [ ] Agent creation works
- [ ] Tool decorators work
- [ ] MCP server connects
- [ ] SKiDL functions work
- [ ] CLI starts without errors
- [ ] Basic pipeline functionality works

### Performance Check
- [ ] Agent creation time similar to before
- [ ] Tool execution time unchanged
- [ ] Memory usage stable
- [ ] No obvious performance regressions

### Documentation Updates
- [ ] Update README if needed
- [ ] Update AGENTS.md if API patterns changed
- [ ] Update any code examples
- [ ] Note version compatibility in docs

## Rollback Plan

If migration fails:
```bash
# Revert dependency changes
git checkout pyproject.toml requirements.txt

# Reinstall old versions
pip install openai-agents==0.1.0 skidl>=2.0.1

# Verify rollback worked
pytest -q tests/
```

## Success Criteria

Migration is successful when:
1. ✅ All existing tests pass
2. ✅ No import errors
3. ✅ All agent creation functions work
4. ✅ Tool decorators work correctly
5. ✅ MCP servers connect successfully
6. ✅ SKiDL integration works
7. ✅ CLI functionality unchanged
8. ✅ Core pipeline features work

## Notes

- OpenAI Agents SDK 0.1.0 → 0.2.10 is a significant jump likely containing breaking changes
- SKiDL 2.0.1 → 2.1.0 is a minor update, fewer breaking changes expected
- Test thoroughly before deploying to production
- Keep the local knowledge base for 0.1.0 as reference during migration