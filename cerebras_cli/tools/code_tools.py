"""Code analysis and execution tools."""

import ast
import sys
import io
import traceback
import contextlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from .base import Tool, ToolParameter, ToolResult, ToolExecutionError


class CodeAnalysisTool(Tool):
    """Tool for analyzing Python code."""
    
    @property
    def name(self) -> str:
        return "code_analyze"
    
    @property
    def description(self) -> str:
        return "Analyze Python code structure and syntax"
    
    @property
    def category(self) -> str:
        return "code"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="code",
            type=str,
            description="Python code to analyze (alternative to file_path)",
            required=False,
            default=None
        ))
        self.add_parameter(ToolParameter(
            name="file_path",
            type=str,
            description="Path to Python file to analyze (alternative to code)",
            required=False,
            default=None
        ))
        self.add_parameter(ToolParameter(
            name="include_ast",
            type=bool,
            description="Include AST dump in analysis",
            required=False,
            default=False
        ))
        self.add_parameter(ToolParameter(
            name="check_syntax",
            type=bool,
            description="Check syntax validity",
            required=False,
            default=True
        ))
    
    async def execute(self, code: Optional[str] = None, file_path: Optional[str] = None,
                     include_ast: bool = False, check_syntax: bool = True) -> ToolResult:
        """Analyze Python code."""
        try:
            # Get source code
            if code is None and file_path is None:
                return ToolResult(
                    success=False,
                    error="Either 'code' or 'file_path' must be provided"
                )
            
            if file_path:
                path = Path(file_path).expanduser().resolve()
                if not path.exists():
                    return ToolResult(
                        success=False,
                        error=f"File not found: {path}"
                    )
                
                with open(path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                source_path = str(path)
            else:
                source_code = code
                source_path = "<string>"
            
            analysis = {
                'source_path': source_path,
                'line_count': len(source_code.splitlines()),
                'char_count': len(source_code),
                'syntax_valid': False,
                'syntax_errors': [],
                'functions': [],
                'classes': [],
                'imports': [],
                'variables': [],
                'complexity': {}
            }
            
            # Parse AST
            try:
                tree = ast.parse(source_code, filename=source_path)
                analysis['syntax_valid'] = True
                
                # Analyze AST
                analyzer = CodeAnalyzer()
                analyzer.visit(tree)
                
                analysis.update({
                    'functions': analyzer.functions,
                    'classes': analyzer.classes,
                    'imports': analyzer.imports,
                    'variables': analyzer.variables,
                    'complexity': {
                        'function_count': len(analyzer.functions),
                        'class_count': len(analyzer.classes),
                        'import_count': len(analyzer.imports),
                        'max_depth': analyzer.max_depth,
                        'cyclomatic_complexity': analyzer.complexity
                    }
                })
                
                if include_ast:
                    analysis['ast_dump'] = ast.dump(tree, indent=2)
                
            except SyntaxError as e:
                analysis['syntax_errors'].append({
                    'line': e.lineno,
                    'column': e.offset,
                    'message': e.msg,
                    'text': e.text
                })
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Failed to parse code: {e}"
                )
            
            return ToolResult(
                success=True,
                data=analysis,
                metadata={
                    'tool': 'code_analyze',
                    'source_type': 'file' if file_path else 'string'
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Code analysis failed: {e}"
            )


class PythonExecuteTool(Tool):
    """Tool for executing Python code safely."""
    
    @property
    def name(self) -> str:
        return "python_exec"
    
    @property
    def description(self) -> str:
        return "Execute Python code in a controlled environment"
    
    @property
    def category(self) -> str:
        return "code"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="code",
            type=str,
            description="Python code to execute",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="timeout",
            type=float,
            description="Execution timeout in seconds",
            required=False,
            default=10.0
        ))
        self.add_parameter(ToolParameter(
            name="capture_output",
            type=bool,
            description="Capture stdout and stderr",
            required=False,
            default=True
        ))
        self.add_parameter(ToolParameter(
            name="globals_dict",
            type=dict,
            description="Global variables for execution",
            required=False,
            default=None
        ))
    
    async def execute(self, code: str, timeout: float = 10.0, 
                     capture_output: bool = True, 
                     globals_dict: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute Python code safely."""
        try:
            # Prepare execution environment
            exec_globals = {
                '__builtins__': {
                    # Safe builtins only
                    'abs': abs, 'all': all, 'any': any, 'ascii': ascii,
                    'bin': bin, 'bool': bool, 'bytearray': bytearray,
                    'bytes': bytes, 'chr': chr, 'complex': complex,
                    'dict': dict, 'divmod': divmod, 'enumerate': enumerate,
                    'filter': filter, 'float': float, 'format': format,
                    'frozenset': frozenset, 'hex': hex, 'int': int,
                    'isinstance': isinstance, 'issubclass': issubclass,
                    'iter': iter, 'len': len, 'list': list, 'map': map,
                    'max': max, 'min': min, 'next': next, 'oct': oct,
                    'ord': ord, 'pow': pow, 'print': print, 'range': range,
                    'repr': repr, 'reversed': reversed, 'round': round,
                    'set': set, 'slice': slice, 'sorted': sorted,
                    'str': str, 'sum': sum, 'tuple': tuple, 'type': type,
                    'zip': zip
                }
            }
            
            if globals_dict:
                exec_globals.update(globals_dict)
            
            # Capture output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            if capture_output:
                captured_stdout = io.StringIO()
                captured_stderr = io.StringIO()
                sys.stdout = captured_stdout
                sys.stderr = captured_stderr
            
            result_data = {}
            error = None
            
            try:
                # Check for dangerous operations
                if self._has_dangerous_operations(code):
                    return ToolResult(
                        success=False,
                        error="Code contains potentially dangerous operations"
                    )
                
                # Compile and execute
                compiled = compile(code, '<string>', 'exec')
                exec_locals = {}
                
                # Execute with timeout (simplified - real implementation would need threading)
                exec(compiled, exec_globals, exec_locals)
                
                # Get results
                if capture_output:
                    result_data['stdout'] = captured_stdout.getvalue()
                    result_data['stderr'] = captured_stderr.getvalue()
                
                # Get local variables (excluding builtins and functions)
                locals_result = {}
                for name, value in exec_locals.items():
                    if not name.startswith('_') and not callable(value):
                        try:
                            # Only include serializable values
                            str(value)  # Test if it can be converted to string
                            locals_result[name] = value
                        except:
                            locals_result[name] = f"<{type(value).__name__}>"
                
                result_data['locals'] = locals_result
                
            except Exception as e:
                error = f"{type(e).__name__}: {str(e)}"
                if capture_output:
                    result_data['stdout'] = captured_stdout.getvalue()
                    result_data['stderr'] = captured_stderr.getvalue()
                result_data['traceback'] = traceback.format_exc()
            
            finally:
                # Restore stdout/stderr
                if capture_output:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
            
            return ToolResult(
                success=error is None,
                data=result_data,
                error=error,
                metadata={
                    'tool': 'python_exec',
                    'timeout': timeout,
                    'captured_output': capture_output
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Execution failed: {e}"
            )
    
    def _has_dangerous_operations(self, code: str) -> bool:
        """Check for potentially dangerous operations."""
        dangerous_keywords = [
            'import os', 'import sys', 'import subprocess', 'import shutil',
            'import socket', 'import urllib', 'import requests',
            'open(', 'file(', 'exec(', 'eval(', '__import__',
            'compile(', 'globals()', 'locals()', 'vars()',
            'delattr', 'setattr', 'getattr', 'hasattr'
        ]
        
        code_lower = code.lower()
        return any(keyword in code_lower for keyword in dangerous_keywords)


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor for code analysis."""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.variables = []
        self.max_depth = 0
        self.current_depth = 0
        self.complexity = 0
    
    def visit_FunctionDef(self, node):
        """Visit function definition."""
        self.functions.append({
            'name': node.name,
            'line': node.lineno,
            'args': [arg.arg for arg in node.args.args],
            'decorators': [ast.dump(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node)
        })
        
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1
    
    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition."""
        self.functions.append({
            'name': node.name,
            'line': node.lineno,
            'args': [arg.arg for arg in node.args.args],
            'decorators': [ast.dump(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node),
            'async': True
        })
        
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1
    
    def visit_ClassDef(self, node):
        """Visit class definition."""
        self.classes.append({
            'name': node.name,
            'line': node.lineno,
            'bases': [ast.dump(base) for base in node.bases],
            'decorators': [ast.dump(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node)
        })
        
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1
    
    def visit_Import(self, node):
        """Visit import statement."""
        for alias in node.names:
            self.imports.append({
                'name': alias.name,
                'asname': alias.asname,
                'line': node.lineno,
                'type': 'import'
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit from...import statement."""
        for alias in node.names:
            self.imports.append({
                'module': node.module,
                'name': alias.name,
                'asname': alias.asname,
                'line': node.lineno,
                'type': 'from_import'
            })
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Visit assignment."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.append({
                    'name': target.id,
                    'line': node.lineno,
                    'type': 'assignment'
                })
        self.generic_visit(node)
    
    def visit_If(self, node):
        """Visit if statement (for complexity)."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        """Visit for loop (for complexity)."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        """Visit while loop (for complexity)."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Visit try statement (for complexity)."""
        self.complexity += 1
        self.generic_visit(node)
