"""Tests for the persona management system."""

import pytest
from core.config import Config
from personas.persona_manager import PersonaManager, Persona


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        github_token="test_token",
        default_persona="senior_developer"
    )


@pytest.fixture
def persona_manager(config):
    """Create a persona manager instance."""
    return PersonaManager(config)


def test_persona_manager_initialization(persona_manager):
    """Test persona manager initialization."""
    assert persona_manager.current_persona is not None
    assert persona_manager.current_persona.name == "Senior Developer"
    assert len(persona_manager.available_personas) > 0


def test_get_available_personas(persona_manager):
    """Test getting available personas."""
    personas = persona_manager.get_available_personas()
    
    assert "senior_developer" in personas
    assert "security_expert" in personas
    assert "ui_ux_specialist" in personas
    assert len(personas) >= 5


def test_set_persona(persona_manager):
    """Test setting persona."""
    # Test valid persona
    result = persona_manager.set_persona("security_expert")
    assert result is True
    assert persona_manager.current_persona.name == "Security Expert"
    
    # Test invalid persona
    result = persona_manager.set_persona("nonexistent_persona")
    assert result is False


def test_get_persona_info(persona_manager):
    """Test getting persona information."""
    info = persona_manager.get_persona_info("senior_developer")
    
    assert info is not None
    assert info["name"] == "Senior Developer"
    assert "expertise_areas" in info
    assert "communication_style" in info
    
    # Test non-existent persona
    info = persona_manager.get_persona_info("nonexistent")
    assert info is None


def test_format_response_with_persona(persona_manager):
    """Test response formatting with persona."""
    persona_manager.set_persona("security_expert")
    
    response = "This code has some issues."
    formatted = persona_manager.format_response_with_persona(response, "analysis")
    
    assert "security" in formatted.lower() or "Security" in formatted


def test_get_persona_suggestions(persona_manager):
    """Test getting persona-specific suggestions."""
    persona_manager.set_persona("security_expert")
    suggestions = persona_manager.get_persona_suggestions("code_review")
    
    assert len(suggestions) > 0
    assert any("security" in s.lower() for s in suggestions)


def test_expertise_match_score(persona_manager):
    """Test expertise matching."""
    persona_manager.set_persona("security_expert")
    
    security_score = persona_manager.get_expertise_match_score("security vulnerability assessment")
    general_score = persona_manager.get_expertise_match_score("general programming")
    
    assert security_score > general_score
    assert 0 <= security_score <= 1
    assert 0 <= general_score <= 1


def test_suggest_persona_for_task(persona_manager):
    """Test persona suggestion for tasks."""
    security_task = "review code for security vulnerabilities"
    suggested = persona_manager.suggest_persona_for_task(security_task)
    assert suggested == "security_expert"
    
    ui_task = "improve user interface design"
    suggested = persona_manager.suggest_persona_for_task(ui_task)
    assert suggested == "ui_ux_specialist"


def test_create_custom_persona(persona_manager):
    """Test creating custom persona."""
    custom_data = {
        "name": "test_persona",
        "description": "A test persona",
        "expertise_areas": ["testing"],
        "communication_style": "casual",
        "response_templates": {},
        "suggested_actions": ["test code"],
        "personality_traits": ["helpful"],
        "preferred_technologies": ["pytest"],
        "focus_areas": ["quality"],
        "example_responses": {}
    }
    
    result = persona_manager.create_custom_persona("Test Persona", custom_data)
    assert result is True
    # Check using the proper key format (lowercase with underscores)
    assert "test_persona" in persona_manager.available_personas
    
    # Test setting the custom persona
    result = persona_manager.set_persona("test_persona")
    assert result is True


def test_persona_dataclass():
    """Test the Persona dataclass."""
    persona = Persona(
        name="Test Persona",
        description="A test persona",
        expertise_areas=["testing"],
        communication_style="formal",
        response_templates={"test": "Test: {response}"},
        suggested_actions=["test"],
        personality_traits=["methodical"],
        preferred_technologies=["python"],
        focus_areas=["quality"],
        example_responses={"greeting": "Hello"}
    )
    
    assert persona.name == "Test Persona"
    assert persona.communication_style == "formal"
    assert "testing" in persona.expertise_areas


def test_communication_style_formatting(persona_manager):
    """Test different communication style formatting."""
    response = "I think you should implement this feature."
    
    # Test formal style
    persona_manager.set_persona("senior_developer")  # formal style
    formatted = persona_manager._make_formal(response)
    assert "I believe" in formatted or "I recommend" in formatted
    
    # Test casual style  
    formatted = persona_manager._make_casual(formatted)
    assert "I'd suggest" in formatted or "You might want" in formatted