#!/usr/bin/env python3
"""
Migration script for OpenAI Agents SDK upgrade from 0.1.0 to 0.2.10
and SKiDL upgrade from 2.0.1 to 2.1.0

This script should be run after installing the updated dependencies to:
1. Test for breaking changes
2. Identify specific issues
3. Apply fixes where needed
4. Validate the upgrade was successful
"""

import sys
import subprocess
import importlib
from pathlib import Path

# Add circuitron to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "circuitron"))

def run_tests():
    """Run the existing test suite to identify breaking changes."""
    print("🧪 Running existing test suite...")
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-q", "tests/"],
            cwd=Path(__file__).parent.parent / "circuitron",
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("  ✅ All tests passed!")
            return True
        else:
            print(f"  ❌ Tests failed (exit code: {result.returncode})")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("  ⏰ Tests timed out")
        return False
    except Exception as e:
        print(f"  💥 Test execution failed: {e}")
        return False

def test_import_compatibility():
    """Test that all imports still work with upgraded packages."""
    print("\n🔄 Testing import compatibility...")
    
    # Test core agent imports
    imports_to_test = [
        "from agents import Agent",
        "from agents import function_tool", 
        "from agents.model_settings import ModelSettings",
        "from agents.tool import Tool",
        "from agents.mcp import MCPServer, MCPServerSse",
        "from agents.result import RunResult",
        "from agents.items import ReasoningItem",
        "import skidl",
    ]
    
    for import_stmt in imports_to_test:
        try:
            exec(import_stmt)
            print(f"  ✅ {import_stmt}")
        except ImportError as e:
            print(f"  ❌ {import_stmt} - ImportError: {e}")
            return False
        except Exception as e:
            print(f"  ⚠️  {import_stmt} - {type(e).__name__}: {e}")
            
    return True

def test_agent_creation():
    """Test that Agent creation still works."""
    print("\n🤖 Testing Agent creation...")
    
    try:
        from agents import Agent
        from agents.model_settings import ModelSettings
        
        # Test basic agent creation
        agent = Agent(
            name="Test-Agent",
            instructions="Test instructions",
            model="gpt-4o",
            model_settings=ModelSettings(tool_choice="required")
        )
        print("  ✅ Basic Agent creation works")
        
        # Test agent with tools and output_type
        agent_with_tools = Agent(
            name="Test-Agent-Tools",
            instructions="Test instructions with tools",
            model="gpt-4o",
            tools=[],
            output_type=str,
            model_settings=ModelSettings()
        )
        print("  ✅ Agent creation with tools and output_type works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Agent creation failed: {e}")
        return False

def test_function_tool_decorator():
    """Test that @function_tool decorator still works."""
    print("\n🔧 Testing @function_tool decorator...")
    
    try:
        from agents import function_tool
        
        @function_tool
        async def test_tool(param: str) -> str:
            """Test tool function."""
            return f"Result: {param}"
            
        print("  ✅ @function_tool decorator works")
        
        # Check if tool has expected attributes
        if hasattr(test_tool, '__name__'):
            print("  ✅ Tool has __name__ attribute")
        
        return True
        
    except Exception as e:
        print(f"  ❌ @function_tool decorator failed: {e}")
        return False

def test_mcp_server():
    """Test MCP server functionality."""
    print("\n🌐 Testing MCP server imports...")
    
    try:
        from agents.mcp import MCPServer, MCPServerSse
        print("  ✅ MCP server imports work")
        return True
        
    except Exception as e:
        print(f"  ❌ MCP server imports failed: {e}")
        return False

def test_skidl_compatibility():
    """Test SKiDL compatibility."""
    print("\n⚡ Testing SKiDL compatibility...")
    
    try:
        import skidl
        print(f"  ✅ SKiDL imported successfully (version: {getattr(skidl, '__version__', 'unknown')})")
        
        # Test basic SKiDL operations
        try:
            from skidl import Part, Net
            print("  ✅ SKiDL basic imports work")
        except ImportError as e:
            print(f"  ❌ SKiDL basic imports failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ SKiDL import failed: {e}")
        return False

def check_circuitron_agents():
    """Test that Circuitron's agent creation functions still work."""
    print("\n🏗️ Testing Circuitron agent creation functions...")
    
    try:
        # Import without actually creating agents (to avoid missing dependencies)
        import circuitron.agents as agents_module
        
        # Check that agent creation functions exist
        expected_functions = [
            'create_planning_agent',
            'create_plan_editor_agent', 
            'create_partfinder_agent',
            'create_partselection_agent',
            'create_documentation_agent',
            'create_code_generation_agent',
            'create_code_validation_agent',
            'create_code_correction_agent',
            'create_runtime_correction_agent',
            'create_erc_handling_agent'
        ]
        
        for func_name in expected_functions:
            if hasattr(agents_module, func_name):
                print(f"  ✅ {func_name} exists")
            else:
                print(f"  ❌ {func_name} missing")
                return False
                
        return True
        
    except Exception as e:
        print(f"  ❌ Circuitron agents import failed: {e}")
        return False

def main():
    """Run all migration tests."""
    print("🚀 Starting OpenAI Agents SDK and SKiDL migration tests...\n")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Import Compatibility", test_import_compatibility()))
    test_results.append(("Agent Creation", test_agent_creation()))
    test_results.append(("Function Tool Decorator", test_function_tool_decorator()))
    test_results.append(("MCP Server", test_mcp_server()))
    test_results.append(("SKiDL Compatibility", test_skidl_compatibility()))
    test_results.append(("Circuitron Agents", check_circuitron_agents()))
    test_results.append(("Existing Test Suite", run_tests()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 MIGRATION TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Migration completed successfully!")
        print("All dependencies have been upgraded without breaking changes.")
        return 0
    else:
        print("⚠️  Migration issues detected!")
        print("Some functionality may be broken and needs manual fixes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())