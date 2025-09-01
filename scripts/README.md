# Dependency Update Scripts and Documentation

This directory contains scripts and documentation for upgrading dependencies:
- openai-agents: 0.1.0 → 0.2.10  
- skidl: 2.0.1 → 2.1.0

## Files

### Scripts
- `complete_upgrade.sh` - Complete automated upgrade process
- `migration_test.py` - Test for breaking changes after upgrade
- `api_comparison.py` - Compare API differences between versions
- `test_compatibility.py` - Test syntax compatibility

### Documentation  
- `MIGRATION_GUIDE.md` - Detailed migration guide and troubleshooting
- `README.md` - This file

## Quick Start

When network connectivity is available, run:

```bash
# Make script executable
chmod +x scripts/complete_upgrade.sh

# Run complete upgrade process
./scripts/complete_upgrade.sh
```

This will:
1. Create a backup branch
2. Install updated dependencies
3. Run API analysis
4. Test for breaking changes
5. Run existing test suite
6. Test CLI functionality
7. Generate comprehensive report

## Manual Process

If automated script fails, follow the manual process in `MIGRATION_GUIDE.md`:

1. Install dependencies manually
2. Run migration tests: `python scripts/migration_test.py`
3. Fix any breaking changes identified
4. Run full test suite: `pytest -q tests/`
5. Validate functionality

## Expected Changes

Based on analysis of current codebase:
- ✅ Agent constructor parameters appear compatible
- ✅ Function tool decorator syntax should work
- ✅ MCP server integration should work
- ✅ SKiDL usage patterns should work

⚠️  **However:** Minor version increase (0.1.0 → 0.2.10) likely contains breaking changes that need testing.

## Rollback Plan

If upgrade fails:
```bash
git checkout pyproject.toml requirements.txt
pip install openai-agents==0.1.0 skidl>=2.0.1
```