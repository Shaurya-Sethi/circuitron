#!/bin/bash
# Complete dependency update execution script
# Run this script after network connectivity is restored

set -e  # Exit on any error

echo "🚀 Starting Complete Dependency Update Process"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run from repository root."
    exit 1
fi

# Backup current state
echo "📦 Creating backup branch..."
git checkout -b "backup-before-upgrade-$(date +%Y%m%d-%H%M%S)" || true
git add -A
git commit -m "Backup before dependency upgrade" || true

# Return to main working branch  
git checkout copilot/fix-198

echo "🔧 Installing updated dependencies..."

# First, try to install the new versions
echo "Installing openai-agents==0.2.10..."
pip install openai-agents==0.2.10 --timeout=120

echo "Installing skidl==2.1.0..."
pip install skidl==2.1.0 --timeout=120

echo "Installing other dependencies..."
pip install -r requirements.txt --timeout=120

echo "✅ Dependencies installed successfully"

# Run API comparison
echo "🔍 Running API comparison analysis..."
python /tmp/api_comparison.py > api_analysis.log 2>&1
echo "  📄 API analysis saved to api_analysis.log"

# Run migration tests
echo "🧪 Running migration tests..."
python /tmp/migration_test.py > migration_test.log 2>&1
migration_exit_code=$?

echo "  📄 Migration test results saved to migration_test.log"

if [ $migration_exit_code -eq 0 ]; then
    echo "✅ Migration tests passed!"
else
    echo "⚠️  Migration tests detected issues. Check migration_test.log"
fi

# Run the existing test suite
echo "🏃 Running existing test suite..."
python -m pytest -q tests/ > test_results.log 2>&1
test_exit_code=$?

echo "  📄 Test results saved to test_results.log"

if [ $test_exit_code -eq 0 ]; then
    echo "✅ All existing tests passed!"
else
    echo "⚠️  Some tests failed. Check test_results.log"
fi

# Try basic CLI functionality
echo "🖥️  Testing CLI functionality..."
python -m circuitron --help > cli_test.log 2>&1
cli_exit_code=$?

if [ $cli_exit_code -eq 0 ]; then
    echo "✅ CLI starts successfully"
else
    echo "⚠️  CLI has issues. Check cli_test.log"
fi

# Generate summary report
echo "📊 Generating summary report..."
cat > dependency_update_report.md << EOF
# Dependency Update Report

**Date:** $(date)
**OpenAI Agents:** 0.1.0 → 0.2.10
**SKiDL:** 2.0.1 → 2.1.0

## Test Results

### Migration Tests
- Status: $([ $migration_exit_code -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Details: See \`migration_test.log\`

### Existing Test Suite
- Status: $([ $test_exit_code -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Details: See \`test_results.log\`

### CLI Functionality
- Status: $([ $cli_exit_code -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Details: See \`cli_test.log\`

### API Analysis
- Details: See \`api_analysis.log\`

## Files Generated
- \`api_analysis.log\` - API comparison between versions
- \`migration_test.log\` - Migration test results
- \`test_results.log\` - Full test suite results
- \`cli_test.log\` - CLI functionality test
- \`dependency_update_report.md\` - This report

## Next Steps
EOF

# Add next steps based on results
if [ $migration_exit_code -eq 0 ] && [ $test_exit_code -eq 0 ] && [ $cli_exit_code -eq 0 ]; then
    cat >> dependency_update_report.md << EOF
✅ **All tests passed!** 
- The dependency update was successful
- No breaking changes detected
- Ready to merge changes

**Recommended actions:**
1. Review the logs for any warnings
2. Test any specific functionality manually if needed
3. Update documentation if required
4. Merge the PR
EOF
else
    cat >> dependency_update_report.md << EOF
⚠️  **Issues detected!**
- Some tests failed or issues were found
- Manual intervention may be required

**Required actions:**
1. Review failed test logs
2. Fix any breaking changes identified
3. Re-run tests until all pass
4. Update code as needed for compatibility

**Common fixes needed:**
- Update Agent constructor parameters
- Fix function_tool decorator usage
- Update MCP server integration
- Fix SKiDL import patterns
EOF
fi

# Display final summary
echo ""
echo "📋 DEPENDENCY UPDATE SUMMARY"
echo "============================"
echo "Migration Tests:  $([ $migration_exit_code -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Existing Tests:   $([ $test_exit_code -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "CLI Test:         $([ $cli_exit_code -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo ""
echo "📄 Generated files:"
echo "  - dependency_update_report.md"
echo "  - api_analysis.log"
echo "  - migration_test.log" 
echo "  - test_results.log"
echo "  - cli_test.log"
echo ""

if [ $migration_exit_code -eq 0 ] && [ $test_exit_code -eq 0 ] && [ $cli_exit_code -eq 0 ]; then
    echo "🎉 SUCCESS: Dependency update completed without issues!"
    exit 0
else
    echo "⚠️  WARNING: Issues detected during dependency update."
    echo "Please review the logs and fix any problems before proceeding."
    exit 1
fi