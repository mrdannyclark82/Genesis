"""Tests for the feature suggester module."""

import pytest
import asyncio
import tempfile
from pathlib import Path

from core.config import Config
from feature_suggester.suggester import FeatureSuggester, FeatureSuggestion


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        github_token="test_token",
        learning_enabled=False,
        enable_external_search=False  # Disable external search for tests
    )


@pytest.fixture
def suggester(config):
    """Create a feature suggester instance."""
    return FeatureSuggester(config)


@pytest.mark.asyncio
async def test_suggest_features_for_python_project(suggester):
    """Test feature suggestions for a Python project."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple Python project structure
        project_path = Path(temp_dir)
        
        # Create a Python file
        (project_path / "main.py").write_text("""
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")
        
        # Create requirements.txt
        (project_path / "requirements.txt").write_text("requests>=2.25.0")
        
        suggestions = await suggester.suggest_features_for_project(str(project_path))
        
        assert len(suggestions) > 0
        assert any("README" in s.name for s in suggestions)
        assert any("Testing" in s.name for s in suggestions)


@pytest.mark.asyncio
async def test_suggest_features_by_category(suggester):
    """Test feature suggestions by category."""
    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions = await suggester.suggest_features_by_category("testing", temp_dir)
        
        # Should return suggestions or empty list, not error
        assert isinstance(suggestions, list)


def test_feature_suggestion_dataclass():
    """Test the FeatureSuggestion dataclass."""
    suggestion = FeatureSuggestion(
        name="Test Feature",
        description="A test feature",
        category="testing",
        implementation_steps=["Step 1", "Step 2"],
        files_to_create=["test.py"],
        files_to_modify=["main.py"],
        dependencies=["pytest"],
        examples=[]
    )
    
    assert suggestion.name == "Test Feature"
    assert suggestion.category == "testing"
    assert suggestion.priority == "medium"  # default value
    assert suggestion.confidence == 0.8  # default value


@pytest.mark.asyncio
async def test_analyze_project_structure(suggester):
    """Test project structure analysis."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create various file types
        (project_path / "main.py").write_text("import flask")
        (project_path / "requirements.txt").write_text("flask>=2.0.0")
        (project_path / "README.md").write_text("# Test Project")
        
        project_info = await suggester._analyze_project_structure(str(project_path))
        
        assert 'python' in project_info['languages']
        assert 'flask' in project_info['frameworks']
        assert project_info['has_docs'] is True
        assert project_info['has_web_interface'] is True


def test_template_applicability(suggester):
    """Test template applicability logic."""
    template = {
        'required_languages': ['python'],
        'excluded_if': {'has_tests': True}
    }
    
    project_info = {
        'languages': {'python', 'javascript'},
        'has_tests': False
    }
    
    assert suggester._is_template_applicable(template, project_info) is True
    
    project_info['has_tests'] = True
    assert suggester._is_template_applicable(template, project_info) is False


def test_priority_scoring(suggester):
    """Test priority scoring system."""
    assert suggester._priority_score('high') == 3
    assert suggester._priority_score('medium') == 2
    assert suggester._priority_score('low') == 1
    assert suggester._priority_score('unknown') == 2  # default