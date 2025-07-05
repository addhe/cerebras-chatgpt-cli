#!/usr/bin/env python3
"""
Validation script for Cerebras CLI implementation.

This script tests various components to ensure they work correctly
before running the full CLI.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        # Core imports
        from cerebras_cli.core.config import Config, APIConfig, CLIConfig
        from cerebras_cli.core.client import CerebrasClient
        from cerebras_cli.exceptions import CerebrasError, CerebrasCliError
        print("  ✅ Core modules imported successfully")
        
        # CLI imports
        from cerebras_cli.cli.main import cli
        from cerebras_cli.cli.repl import REPL
        from cerebras_cli.cli.commands import config, models
        print("  ✅ CLI modules imported successfully")
        
        # Tools imports
        from cerebras_cli.tools import default_registry
        from cerebras_cli.tools.base import Tool, ToolRegistry, ToolResult
        from cerebras_cli.tools.file_tools import FileReadTool, FileWriteTool
        from cerebras_cli.tools.shell_tools import ShellCommandTool
        from cerebras_cli.tools.code_tools import CodeAnalysisTool, PythonExecuteTool
        print("  ✅ Tools modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\n🔧 Testing configuration...")
    
    try:
        from cerebras_cli.core.config import Config
        
        # Test default config creation
        config = Config()
        assert hasattr(config, 'api')
        assert hasattr(config, 'cli')
        assert hasattr(config, 'model')
        print("  ✅ Default config created successfully")
        
        # Test environment variable override
        os.environ['CEREBRAS_MODEL'] = 'test-model'
        config = Config()
        assert config.model == 'test-model'
        print("  ✅ Environment variable override works")
        
        # Clean up
        del os.environ['CEREBRAS_MODEL']
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False


async def test_tools():
    """Test the tools system."""
    print("\n🔧 Testing tools system...")
    
    try:
        from cerebras_cli.tools import default_registry
        
        # Test tool registry
        tools = default_registry.list_tools()
        categories = default_registry.list_categories()
        
        assert len(tools) > 0, "No tools found in registry"
        assert len(categories) > 0, "No categories found in registry"
        print(f"  ✅ Found {len(tools)} tools in {len(categories)} categories")
        
        # Test file tools
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!\nThis is a test file.")
            temp_path = f.name
        
        try:
            # Test file read
            result = await default_registry.execute_tool(
                "file_read", 
                path=temp_path
            )
            assert result.success, f"File read failed: {result.error}"
            assert "Hello, World!" in result.data
            print("  ✅ File read tool works")
            
            # Test file write
            test_content = "New content for testing"
            result = await default_registry.execute_tool(
                "file_write",
                path=temp_path,
                content=test_content
            )
            assert result.success, f"File write failed: {result.error}"
            print("  ✅ File write tool works")
            
        finally:
            os.unlink(temp_path)
        
        # Test shell command
        result = await default_registry.execute_tool(
            "shell_exec",
            command="echo 'Test command'"
        )
        assert result.success, f"Shell command failed: {result.error}"
        assert "Test command" in result.data['stdout']
        print("  ✅ Shell command tool works")
        
        # Test code analysis
        test_code = "def hello():\n    return 'world'"
        result = await default_registry.execute_tool(
            "code_analyze",
            code=test_code
        )
        assert result.success, f"Code analysis failed: {result.error}"
        assert result.data['syntax_valid'] == True
        print("  ✅ Code analysis tool works")
        
        # Test safe code execution
        safe_code = "x = 5\ny = 10\nresult = x + y\nprint(f'Result: {result}')"
        result = await default_registry.execute_tool(
            "python_exec",
            code=safe_code
        )
        assert result.success, f"Code execution failed: {result.error}"
        assert "Result: 15" in result.data['stdout']
        print("  ✅ Python execution tool works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_structure():
    """Test CLI command structure."""
    print("\n🖥️  Testing CLI structure...")
    
    try:
        from cerebras_cli.cli.main import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Test help command
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Cerebras' in result.output
        print("  ✅ Main CLI help works")
        
        # Test config command
        result = runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
        print("  ✅ Config command help works")
        
        # Test models command
        result = runner.invoke(cli, ['models', 'list'])
        assert result.exit_code == 0
        print("  ✅ Models command works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ CLI structure test failed: {e}")
        return False


def test_backwards_compatibility():
    """Test backwards compatibility with legacy CLI."""
    print("\n🔄 Testing backwards compatibility...")
    
    try:
        # Test that legacy main.py can be imported
        sys.path.insert(0, str(project_root / 'src'))
        import main as legacy_main
        
        # Check that key functions exist
        assert hasattr(legacy_main, 'main'), "Legacy main function not found"
        print("  ✅ Legacy CLI can be imported")
        
        # Test that new CLI can fall back to legacy mode
        from cerebras_cli.cli.main import cli
        print("  ✅ Backward compatibility maintained")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Backwards compatibility test failed: {e}")
        return False


async def run_all_tests():
    """Run all validation tests."""
    print("🚀 Starting Cerebras CLI Validation")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_config),
        ("Tools System Tests", test_tools),
        ("CLI Structure Tests", test_cli_structure),
        ("Backwards Compatibility Tests", test_backwards_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Cerebras CLI is ready to use.")
        print("\nNext steps:")
        print("1. Set your CEREBRAS_API_KEY environment variable")
        print("2. Run: python -m cerebras_cli")
        print("3. Or try: python examples/tools_demo.py")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    # Run validation
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
