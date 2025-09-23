"""Tests for enhanced natural language processing."""

import pytest
import asyncio
from core.agent import GenesisAgent
from core.config import Config


class TestNaturalLanguageProcessing:
    """Test natural language processing enhancements."""

    @pytest.fixture
    def agent(self):
        """Create a test agent without GitHub client initialization."""
        config = Config(
            github_token='test_token',
            learning_enabled=False
        )
        
        # Create agent but don't initialize GitHub client for testing
        agent = GenesisAgent.__new__(GenesisAgent)
        agent.config = config
        return agent

    @pytest.mark.asyncio
    async def test_intent_parsing_suggest(self, agent):
        """Test intent parsing for suggest commands."""
        test_cases = [
            "suggest improvements",
            "recommend changes", 
            "make it better",
            "what can be improved",
            "how to improve this"
        ]
        
        for command in test_cases:
            intent = await agent._parse_intent(command)
            assert intent['action'] == 'suggest'

    @pytest.mark.asyncio
    async def test_intent_parsing_implement(self, agent):
        """Test intent parsing for implement commands."""
        test_cases = [
            "implement suggestions",
            "apply changes",
            "implement changes",
            "apply suggestions",
            "go ahead and fix it"
        ]
        
        for command in test_cases:
            intent = await agent._parse_intent(command)
            assert intent['action'] == 'implement'

    @pytest.mark.asyncio
    async def test_intent_parsing_analyze(self, agent):
        """Test intent parsing for analyze commands."""
        test_cases = [
            "analyze the code",
            "check this file",
            "review my code",
            "scan for issues",
            "examine the codebase"
        ]
        
        for command in test_cases:
            intent = await agent._parse_intent(command)
            assert intent['action'] == 'analyze'

    @pytest.mark.asyncio
    async def test_intent_parsing_help(self, agent):
        """Test intent parsing for help commands."""
        test_cases = [
            "help",
            "what can you do",
            "commands",
            "help me"
        ]
        
        for command in test_cases:
            intent = await agent._parse_intent(command)
            assert intent['action'] == 'help'

    @pytest.mark.asyncio
    async def test_intent_parsing_status(self, agent):
        """Test intent parsing for status commands."""
        test_cases = [
            "status",
            "how are you",
            "what are you doing"
        ]
        
        for command in test_cases:
            intent = await agent._parse_intent(command)
            assert intent['action'] == 'status'

    def test_help_message_generation(self, agent):
        """Test help message generation."""
        help_message = agent._get_help_message()
        
        assert "Analysis Commands" in help_message
        assert "Suggestion Commands" in help_message
        assert "Implementation Commands" in help_message
        assert "Information Commands" in help_message
        assert "suggest improvements" in help_message
        assert "implement suggestions" in help_message

    @pytest.mark.asyncio
    async def test_target_extraction(self, agent):
        """Test target extraction from commands."""
        test_cases = [
            ("analyze main.py", "main.py"),
            ("check this file", "file"),
            ("review current directory", "directory"),
            ("analyze the code", ".")
        ]
        
        for command, expected_target in test_cases:
            target = agent._extract_target(command)
            assert target == expected_target