"""Code analyzer for generating suggestions and improvements."""

import ast
import os
import re
import json
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from core.config import Config
from utils.logger import get_logger


@dataclass
class CodeIssue:
    """Represents a code issue or suggestion."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    message: str
    suggestion: str
    confidence: float = 0.8


@dataclass
class CodeMetrics:
    """Code quality metrics."""
    lines_of_code: int
    cyclomatic_complexity: int
    maintainability_index: float
    code_duplication: float
    test_coverage: float = 0.0


class CodeAnalyzer:
    """Analyzes code and generates improvement suggestions."""
    
    def __init__(self, config: Config):
        """Initialize the code analyzer."""
        self.config = config
        self.logger = get_logger(__name__)
        self.pending_suggestions: List[Dict[str, Any]] = []
        
        # Supported file extensions
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
        }
        
        self.logger.info("Code analyzer initialized")
    
    async def analyze_path(self, path: str) -> List[str]:
        """Analyze code at the specified path."""
        path_obj = Path(path)
        results = []
        
        if path_obj.is_file():
            if path_obj.suffix in self.supported_extensions:
                file_results = await self._analyze_file(str(path_obj))
                results.extend(file_results)
            else:
                results.append(f"Unsupported file type: {path_obj.suffix}")
        
        elif path_obj.is_dir():
            for file_path in self._get_code_files(path_obj):
                file_results = await self._analyze_file(str(file_path))
                results.extend(file_results)
        
        else:
            results.append(f"Path not found: {path}")
        
        return results if results else ["No issues found"]
    
    async def suggest_improvements(self, path: str = ".") -> List[str]:
        """Generate improvement suggestions for code."""
        suggestions = []
        path_obj = Path(path)
        
        # Analyze code structure and patterns
        if path_obj.exists():
            issues = await self._find_code_issues(path_obj)
            
            for issue in issues:
                suggestion_text = self._format_suggestion(issue)
                suggestions.append(suggestion_text)
                
                # Store for potential implementation
                self.pending_suggestions.append({
                    'type': issue.issue_type,
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'message': issue.message,
                    'suggestion': issue.suggestion,
                    'confidence': issue.confidence,
                    'timestamp': datetime.now().isoformat(),
                })
        
        return suggestions if suggestions else ["No improvements suggested"]
    
    async def suggest_improvements_for_repo(self, repo_info: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions for a GitHub repository."""
        suggestions = []
        
        # Analyze repository structure
        languages = repo_info.get('languages', {})
        topics = repo_info.get('topics', [])
        
        # General repository suggestions
        if not repo_info.get('description'):
            suggestions.append("Add a clear repository description")
        
        if 'README.md' not in str(repo_info):
            suggestions.append("Add a comprehensive README.md file")
        
        if not topics:
            suggestions.append("Add relevant topics to improve discoverability")
        
        # Language-specific suggestions
        if 'Python' in languages:
            suggestions.extend(await self._get_python_repo_suggestions(repo_info))
        
        if 'JavaScript' in languages:
            suggestions.extend(await self._get_javascript_repo_suggestions(repo_info))
        
        return suggestions
    
    async def get_pending_suggestions(self) -> List[Dict[str, Any]]:
        """Get pending suggestions for implementation."""
        return self.pending_suggestions.copy()
    
    async def clear_pending_suggestions(self) -> None:
        """Clear pending suggestions."""
        self.pending_suggestions.clear()
    
    async def _analyze_file(self, file_path: str) -> List[str]:
        """Analyze a single file."""
        results = []
        file_ext = Path(file_path).suffix
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_ext == '.py':
                results.extend(await self._analyze_python_file(file_path, content))
            elif file_ext in ['.js', '.ts']:
                results.extend(await self._analyze_javascript_file(file_path, content))
            else:
                results.extend(await self._analyze_generic_file(file_path, content))
                
        except Exception as e:
            results.append(f"Error analyzing {file_path}: {str(e)}")
        
        return results
    
    async def _analyze_python_file(self, file_path: str, content: str) -> List[str]:
        """Analyze a Python file."""
        results = []
        
        try:
            tree = ast.parse(content)
            
            # Check for missing docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        results.append(f"Missing docstring in {node.name} at line {node.lineno}")
            
            # Check for long functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        results.append(f"Function {node.name} is too long ({func_lines} lines) at line {node.lineno}")
            
            # Check for complex conditions
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    complexity = self._calculate_condition_complexity(node.test)
                    if complexity > 5:
                        results.append(f"Complex condition at line {node.lineno} (complexity: {complexity})")
            
        except SyntaxError as e:
            results.append(f"Syntax error: {str(e)}")
        
        return results
    
    async def _analyze_javascript_file(self, file_path: str, content: str) -> List[str]:
        """Analyze a JavaScript/TypeScript file."""
        results = []
        
        lines = content.split('\n')
        
        # Check for console.log statements
        for i, line in enumerate(lines, 1):
            if 'console.log' in line:
                results.append(f"Console.log statement at line {i} - consider using proper logging")
        
        # Check for var usage (should use let/const)
        for i, line in enumerate(lines, 1):
            if re.search(r'\bvar\s+\w+', line):
                results.append(f"Use 'let' or 'const' instead of 'var' at line {i}")
        
        # Check for function length
        function_starts = []
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            if 'function' in line or '=>' in line:
                function_starts.append(i)
            
            brace_count += line.count('{') - line.count('}')
            
            if brace_count == 0 and function_starts:
                func_length = i - function_starts[-1]
                if func_length > 50:
                    results.append(f"Long function starting at line {function_starts[-1]} ({func_length} lines)")
                function_starts.pop()
        
        return results
    
    async def _analyze_generic_file(self, file_path: str, content: str) -> List[str]:
        """Analyze a generic code file."""
        results = []
        
        lines = content.split('\n')
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                results.append(f"Long line at {i} ({len(line)} characters)")
        
        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.endswith(' ') or line.endswith('\t'):
                results.append(f"Trailing whitespace at line {i}")
        
        # Check for mixed indentation
        has_tabs = any('\t' in line for line in lines)
        has_spaces = any(line.startswith('    ') for line in lines)
        
        if has_tabs and has_spaces:
            results.append("Mixed indentation detected (tabs and spaces)")
        
        return results
    
    async def _find_code_issues(self, path: Path) -> List[CodeIssue]:
        """Find code issues and generate structured suggestions."""
        issues = []
        
        for file_path in self._get_code_files(path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_issues = await self._analyze_file_for_issues(str(file_path), content)
                issues.extend(file_issues)
                
            except Exception as e:
                self.logger.error(f"Error analyzing {file_path}: {e}")
        
        return issues
    
    async def _analyze_file_for_issues(self, file_path: str, content: str) -> List[CodeIssue]:
        """Analyze file content for specific issues."""
        issues = []
        lines = content.split('\n')
        file_ext = Path(file_path).suffix
        
        # Common issues across all languages
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 120:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type='style',
                    severity='low',
                    message=f'Line too long ({len(line)} characters)',
                    suggestion='Consider breaking this line into multiple lines',
                    confidence=0.9
                ))
            
            # TODO comments
            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type='maintenance',
                    severity='medium',
                    message='TODO/FIXME comment found',
                    suggestion='Address this TODO item or convert to proper issue tracking',
                    confidence=0.7
                ))
        
        # Language-specific issues
        if file_ext == '.py':
            issues.extend(await self._analyze_python_issues(file_path, content))
        elif file_ext in ['.js', '.ts']:
            issues.extend(await self._analyze_javascript_issues(file_path, content))
        
        return issues
    
    async def _analyze_python_issues(self, file_path: str, content: str) -> List[CodeIssue]:
        """Analyze Python-specific issues."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node):
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type='documentation',
                            severity='medium',
                            message=f'Function {node.name} missing docstring',
                            suggestion=f'Add docstring to explain what {node.name} does',
                            confidence=0.8
                        ))
                
                elif isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type='documentation',
                            severity='medium',
                            message=f'Class {node.name} missing docstring',
                            suggestion=f'Add docstring to explain what {node.name} represents',
                            confidence=0.8
                        ))
        
        except SyntaxError:
            # Skip files with syntax errors
            pass
        
        return issues
    
    async def _analyze_javascript_issues(self, file_path: str, content: str) -> List[CodeIssue]:
        """Analyze JavaScript-specific issues."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'console.log' in line:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type='debugging',
                    severity='low',
                    message='Console.log statement found',
                    suggestion='Remove console.log or replace with proper logging',
                    confidence=0.9
                ))
        
        return issues
    
    def _get_code_files(self, path: Path) -> List[Path]:
        """Get all code files in a directory."""
        if path.is_file():
            return [path] if path.suffix in self.supported_extensions else []
        
        code_files = []
        for file_path in path.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in self.supported_extensions and
                not self._should_ignore_file(file_path)):
                code_files.append(file_path)
        
        return code_files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        ignore_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            '.venv',
            'venv',
            '.pytest_cache',
            'dist',
            'build',
            '.mypy_cache',
        ]
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
    
    def _calculate_condition_complexity(self, node: ast.AST) -> int:
        """Calculate complexity of a condition."""
        if isinstance(node, ast.BoolOp):
            return 1 + sum(self._calculate_condition_complexity(value) for value in node.values)
        elif isinstance(node, ast.Compare):
            return len(node.ops)
        else:
            return 1
    
    def _format_suggestion(self, issue: CodeIssue) -> str:
        """Format a code issue as a suggestion string."""
        return f"{issue.file_path}:{issue.line_number} - {issue.message} ({issue.severity})"
    
    async def _get_python_repo_suggestions(self, repo_info: Dict[str, Any]) -> List[str]:
        """Get Python-specific repository suggestions."""
        suggestions = []
        
        # Check for common Python files
        suggestions.append("Consider adding requirements.txt for dependency management")
        suggestions.append("Add setup.py or pyproject.toml for package configuration")
        suggestions.append("Include .gitignore with Python-specific patterns")
        suggestions.append("Add pytest configuration for testing")
        
        return suggestions
    
    async def _get_javascript_repo_suggestions(self, repo_info: Dict[str, Any]) -> List[str]:
        """Get JavaScript-specific repository suggestions."""
        suggestions = []
        
        suggestions.append("Consider adding package.json for dependency management")
        suggestions.append("Add .eslintrc for code linting")
        suggestions.append("Include .gitignore with Node.js-specific patterns")
        suggestions.append("Add Jest or Mocha configuration for testing")
        
        return suggestions