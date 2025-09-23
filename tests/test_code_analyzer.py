"""Tests for code analyzer module."""

import tempfile
from pathlib import Path

import pytest

from core.config import Config
from code_analyzer.analyzer import CodeAnalyzer, CodeIssue


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        github_token='test_token',
        learning_enabled=False  # Disable learning for tests
    )


@pytest.fixture
def analyzer(config):
    """Create code analyzer instance."""
    return CodeAnalyzer(config)


def test_analyze_python_file(analyzer):
    """Test analyzing a Python file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def function_without_docstring():
    pass

class ClassWithoutDocstring:
    pass

def function_with_long_line():
    very_long_line = "This is a very long line that exceeds the recommended length limit and should be flagged by the analyzer"
    return very_long_line
""")
        f.flush()
        
        # Test file analysis
        results = analyzer.analyze_path(f.name)
        
        # Should find missing docstrings and long line
        assert len(results) > 0
        
        # Clean up
        Path(f.name).unlink()


def test_analyze_javascript_file(analyzer):
    """Test analyzing a JavaScript file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write("""
console.log("Debug statement");

var oldVar = "should use let or const";

function longFunction() {
    // This function has many lines
    console.log("Line 1");
    console.log("Line 2");
    // ... imagine many more lines
}
""")
        f.flush()
        
        # Test file analysis
        results = analyzer.analyze_path(f.name)
        
        # Should find console.log and var usage
        assert len(results) > 0
        
        # Clean up
        Path(f.name).unlink()


def test_suggest_improvements(analyzer):
    """Test improvement suggestions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a Python file with issues
        py_file = Path(temp_dir) / 'test.py'
        py_file.write_text("""
def bad_function():
    # TODO: Add proper implementation
    pass
""")
        
        # Test suggestions
        suggestions = analyzer.suggest_improvements(temp_dir)
        
        assert len(suggestions) > 0
        assert any('docstring' in s.lower() or 'todo' in s.lower() for s in suggestions)


def test_code_issue_creation():
    """Test CodeIssue dataclass creation."""
    issue = CodeIssue(
        file_path="/test/file.py",
        line_number=10,
        issue_type="documentation",
        severity="medium",
        message="Missing docstring",
        suggestion="Add docstring",
        confidence=0.8
    )
    
    assert issue.file_path == "/test/file.py"
    assert issue.line_number == 10
    assert issue.confidence == 0.8


def test_supported_file_extensions(analyzer):
    """Test that analyzer recognizes supported file extensions."""
    assert '.py' in analyzer.supported_extensions
    assert '.js' in analyzer.supported_extensions
    assert '.java' in analyzer.supported_extensions
    assert analyzer.supported_extensions['.py'] == 'python'


def test_ignore_patterns(analyzer):
    """Test that certain files are ignored."""
    # Create test paths
    test_paths = [
        Path('__pycache__/test.py'),
        Path('.git/config'),
        Path('node_modules/package.js'),
        Path('regular_file.py'),
    ]
    
    ignored_count = sum(1 for path in test_paths if analyzer._should_ignore_file(path))
    
    # Should ignore first 3 paths
    assert ignored_count == 3