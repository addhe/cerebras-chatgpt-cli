#!/usr/bin/env python3
"""
Example script demonstrating the Cerebras CLI tools system.

This script shows how to use the various tools available in the CLI
without starting the full interactive REPL.
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cerebras_cli.tools import default_registry


async def demonstrate_file_tools():
    """Demonstrate file manipulation tools."""
    print("🔧 File Tools Demo")
    print("=" * 50)
    
    # Create a temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 1. File Write Tool
        print("\n1. Writing a file...")
        file_path = temp_path / "demo.py"
        content = '''#!/usr/bin/env python3
"""Demo Python script."""

def greet(name="World"):
    """Greet someone."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("Cerebras CLI"))
'''
        
        result = await default_registry.execute_tool(
            "file_write",
            path=str(file_path),
            content=content
        )
        
        if result.success:
            print(f"✅ File written: {file_path}")
        else:
            print(f"❌ Error: {result.error}")
        
        # 2. File Read Tool
        print("\n2. Reading the file...")
        result = await default_registry.execute_tool(
            "file_read",
            path=str(file_path)
        )
        
        if result.success:
            print("✅ File content:")
            print("─" * 30)
            print(result.data)
            print("─" * 30)
        else:
            print(f"❌ Error: {result.error}")
        
        # 3. File List Tool
        print("\n3. Listing directory contents...")
        result = await default_registry.execute_tool(
            "file_list",
            path=str(temp_path)
        )
        
        if result.success:
            print("✅ Directory contents:")
            for item in result.data:
                file_type = "📁" if item['is_dir'] else "📄"
                print(f"  {file_type} {item['name']} ({item.get('size', 'N/A')} bytes)")
        else:
            print(f"❌ Error: {result.error}")


async def demonstrate_shell_tools():
    """Demonstrate shell command tools."""
    print("\n\n🔧 Shell Tools Demo")
    print("=" * 50)
    
    # 1. Simple command
    print("\n1. Running a simple command...")
    result = await default_registry.execute_tool(
        "shell_exec",
        command="echo 'Hello from shell!'"
    )
    
    if result.success:
        print("✅ Command output:")
        print(f"  stdout: {result.data['stdout'].strip()}")
        print(f"  return code: {result.data['returncode']}")
    else:
        print(f"❌ Error: {result.error}")
    
    # 2. Directory operations
    print("\n2. Directory operations...")
    
    # Get current directory
    result = await default_registry.execute_tool("directory", operation="current")
    if result.success:
        print(f"✅ Current directory: {result.data}")
    
    # Create a test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = os.path.join(temp_dir, "test_subdir")
        
        result = await default_registry.execute_tool(
            "directory",
            operation="create",
            path=test_dir
        )
        
        if result.success:
            print(f"✅ Created directory: {test_dir}")
        else:
            print(f"❌ Error creating directory: {result.error}")


async def demonstrate_code_tools():
    """Demonstrate code analysis and execution tools."""
    print("\n\n🔧 Code Tools Demo")
    print("=" * 50)
    
    # 1. Code Analysis
    print("\n1. Analyzing Python code...")
    sample_code = '''
import math
from typing import List

def fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def get_history(self) -> List[str]:
        return self.history.copy()

# Usage example
calc = Calculator()
result = calc.add(5, 3)
fib_10 = fibonacci(10)
'''
    
    result = await default_registry.execute_tool(
        "code_analyze",
        code=sample_code
    )
    
    if result.success:
        analysis = result.data
        print("✅ Code analysis completed:")
        print(f"  📊 Lines: {analysis['line_count']}")
        print(f"  ✅ Syntax valid: {analysis['syntax_valid']}")
        print(f"  🔧 Functions: {len(analysis['functions'])}")
        print(f"  🏗️  Classes: {len(analysis['classes'])}")
        print(f"  📦 Imports: {len(analysis['imports'])}")
        
        if analysis['functions']:
            print("  📋 Functions found:")
            for func in analysis['functions']:
                args_str = ", ".join(func['args'])
                print(f"    • {func['name']}({args_str}) - line {func['line']}")
        
        if analysis['classes']:
            print("  📋 Classes found:")
            for cls in analysis['classes']:
                print(f"    • {cls['name']} - line {cls['line']}")
    else:
        print(f"❌ Error: {result.error}")
    
    # 2. Safe Code Execution
    print("\n2. Executing safe Python code...")
    safe_code = '''
# Simple calculations
x = 10
y = 20
sum_result = x + y
product = x * y

# String operations
message = f"Sum: {sum_result}, Product: {product}"
print(message)

# List operations
numbers = [1, 2, 3, 4, 5]
squared = [n**2 for n in numbers]
print(f"Original: {numbers}")
print(f"Squared: {squared}")
'''
    
    result = await default_registry.execute_tool(
        "python_exec",
        code=safe_code
    )
    
    if result.success:
        print("✅ Code executed successfully:")
        if result.data['stdout']:
            print("  📤 Output:")
            for line in result.data['stdout'].strip().split('\n'):
                print(f"    {line}")
        
        if result.data['locals']:
            print("  🔧 Variables created:")
            for name, value in result.data['locals'].items():
                print(f"    {name} = {value}")
    else:
        print(f"❌ Error: {result.error}")


async def demonstrate_tool_help():
    """Demonstrate the help system."""
    print("\n\n🔧 Help System Demo")
    print("=" * 50)
    
    # List all tools
    print("\n1. Available tools:")
    tools = default_registry.list_tools()
    categories = default_registry.list_categories()
    
    print(f"📊 Total tools: {len(tools)}")
    print(f"📂 Categories: {', '.join(categories)}")
    
    # Show help for each category
    for category in categories:
        print(f"\n📂 {category.upper()} TOOLS:")
        category_tools = default_registry.get_tools_by_category(category)
        for tool in category_tools:
            print(f"  • {tool.name}: {tool.description}")
    
    # Show detailed help for one tool
    print("\n2. Detailed help for file_read tool:")
    print("─" * 40)
    file_read_tool = default_registry.get_tool("file_read")
    if file_read_tool:
        print(file_read_tool.get_help())


async def main():
    """Run all demonstrations."""
    print("🚀 Cerebras CLI Tools Demonstration")
    print("=" * 60)
    
    try:
        await demonstrate_file_tools()
        await demonstrate_shell_tools()
        await demonstrate_code_tools()
        await demonstrate_tool_help()
        
        print("\n\n✅ All demonstrations completed successfully!")
        print("\nTo use these tools interactively, start the CLI with:")
        print("  python -m cerebras_cli")
        print("\nThen use commands like:")
        print("  /tools                    # List all tools")
        print("  /tool file_read path=myfile.py")
        print("  /tool shell_exec command='ls -la'")
        print("  /tool code_analyze code='def hello(): pass'")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
