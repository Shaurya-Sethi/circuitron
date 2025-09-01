#!/usr/bin/env python3
"""
API Comparison Script

This script helps identify specific API changes between old and new versions
of the dependencies by comparing available attributes and methods.
"""

import sys
import inspect
from typing import Any, Dict, Set

def compare_module_apis(old_module: Any, new_module: Any, module_name: str) -> Dict[str, Any]:
    """Compare APIs between old and new module versions."""
    print(f"\n🔍 Comparing {module_name} API changes...")
    
    # Get all public attributes
    old_attrs = {name for name in dir(old_module) if not name.startswith('_')}
    new_attrs = {name for name in dir(new_module) if not name.startswith('_')}
    
    added = new_attrs - old_attrs
    removed = old_attrs - new_attrs
    common = old_attrs & new_attrs
    
    print(f"  📊 Summary for {module_name}:")
    print(f"    Added: {len(added)} items")
    print(f"    Removed: {len(removed)} items") 
    print(f"    Common: {len(common)} items")
    
    if added:
        print(f"  ➕ Added in new version:")
        for item in sorted(added):
            print(f"    + {item}")
    
    if removed:
        print(f"  ➖ Removed in new version:")
        for item in sorted(removed):
            print(f"    - {item}")
    
    # Check for signature changes in common items
    signature_changes = []
    for name in common:
        try:
            old_obj = getattr(old_module, name)
            new_obj = getattr(new_module, name)
            
            if callable(old_obj) and callable(new_obj):
                try:
                    old_sig = inspect.signature(old_obj)
                    new_sig = inspect.signature(new_obj)
                    
                    if old_sig != new_sig:
                        signature_changes.append((name, str(old_sig), str(new_sig)))
                except (ValueError, TypeError):
                    # Some callables don't have inspectable signatures
                    pass
        except Exception:
            pass
    
    if signature_changes:
        print(f"  🔄 Signature changes:")
        for name, old_sig, new_sig in signature_changes:
            print(f"    {name}:")
            print(f"      Old: {old_sig}")
            print(f"      New: {new_sig}")
    
    return {
        'added': added,
        'removed': removed,
        'common': common,
        'signature_changes': signature_changes
    }

def compare_class_apis(old_class: type, new_class: type, class_name: str) -> Dict[str, Any]:
    """Compare APIs between old and new class versions."""
    print(f"\n🏗️ Comparing {class_name} class changes...")
    
    old_methods = {name for name, obj in inspect.getmembers(old_class) 
                   if not name.startswith('_') and callable(obj)}
    new_methods = {name for name, obj in inspect.getmembers(new_class) 
                   if not name.startswith('_') and callable(obj)}
    
    old_attrs = {name for name in dir(old_class) 
                 if not name.startswith('_') and not callable(getattr(old_class, name))}
    new_attrs = {name for name in dir(new_class) 
                 if not name.startswith('_') and not callable(getattr(new_class, name))}
    
    added_methods = new_methods - old_methods
    removed_methods = old_methods - new_methods
    common_methods = old_methods & new_methods
    
    added_attrs = new_attrs - old_attrs
    removed_attrs = old_attrs - new_attrs
    
    print(f"  📊 Summary for {class_name}:")
    print(f"    Methods: +{len(added_methods)} -{len(removed_methods)} ={len(common_methods)}")
    print(f"    Attributes: +{len(added_attrs)} -{len(removed_attrs)}")
    
    if added_methods:
        print(f"  ➕ Added methods:")
        for method in sorted(added_methods):
            print(f"    + {method}")
    
    if removed_methods:
        print(f"  ➖ Removed methods:")
        for method in sorted(removed_methods):
            print(f"    - {method}")
    
    if added_attrs:
        print(f"  ➕ Added attributes:")
        for attr in sorted(added_attrs):
            print(f"    + {attr}")
    
    if removed_attrs:
        print(f"  ➖ Removed attributes:")
        for attr in sorted(removed_attrs):
            print(f"    - {attr}")
    
    return {
        'added_methods': added_methods,
        'removed_methods': removed_methods,
        'added_attrs': added_attrs,
        'removed_attrs': removed_attrs
    }

def check_agent_constructor_changes():
    """Check for changes in Agent constructor."""
    print("\n🤖 Checking Agent constructor changes...")
    
    try:
        from agents import Agent
        
        # Get constructor signature
        sig = inspect.signature(Agent.__init__)
        print(f"  Agent.__init__ signature: {sig}")
        
        # List all parameters
        params = list(sig.parameters.keys())
        print(f"  Parameters ({len(params)}): {', '.join(params)}")
        
        # Check for dataclass fields if it's a dataclass
        if hasattr(Agent, '__dataclass_fields__'):
            fields = Agent.__dataclass_fields__.keys()
            print(f"  Dataclass fields ({len(fields)}): {', '.join(fields)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to analyze Agent constructor: {e}")
        return False

def check_function_tool_changes():
    """Check for changes in function_tool decorator."""
    print("\n🔧 Checking function_tool decorator changes...")
    
    try:
        from agents import function_tool
        
        # Get decorator signature
        sig = inspect.signature(function_tool)
        print(f"  function_tool signature: {sig}")
        
        # Check what it returns
        print(f"  function_tool type: {type(function_tool)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to analyze function_tool: {e}")
        return False

def main():
    """Run API comparison checks."""
    print("🔍 OpenAI Agents SDK & SKiDL API Comparison Tool")
    print("=" * 60)
    
    # Test basic imports first
    try:
        import agents
        print("✅ agents module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import agents: {e}")
        return 1
    
    try:
        import skidl
        print(f"✅ skidl module imported successfully (version: {getattr(skidl, '__version__', 'unknown')})")
    except ImportError as e:
        print(f"❌ Failed to import skidl: {e}")
        print("⚠️  Continuing with agents analysis only...")
    
    # Check specific API changes
    success = True
    success &= check_agent_constructor_changes()
    success &= check_function_tool_changes()
    
    # Try to compare specific classes
    try:
        from agents import Agent
        from agents.model_settings import ModelSettings
        
        print("\n📋 Agent class analysis:")
        agent_info = compare_class_apis(Agent, Agent, "Agent")
        
        print("\n⚙️ ModelSettings class analysis:")
        model_settings_info = compare_class_apis(ModelSettings, ModelSettings, "ModelSettings")
        
    except Exception as e:
        print(f"❌ Class analysis failed: {e}")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ API analysis completed successfully")
        print("Check the output above for any breaking changes")
    else:
        print("❌ API analysis encountered issues")
        print("Some functionality may be broken")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())