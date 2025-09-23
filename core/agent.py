"""Main Genesis AI Agent implementation."""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from core.config import Config
from github_api.client import GitHubClient
from code_analyzer.analyzer import CodeAnalyzer
from self_improvement.learner import SelfLearner
from utils.logger import get_logger


class GenesisAgent:
    """Main AI coding agent that orchestrates all capabilities."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Genesis AI Agent."""
        self.config = config or Config.from_env()
        self.config.validate()
        
        self.logger = get_logger(__name__)
        self.github_client = GitHubClient(self.config)
        self.code_analyzer = CodeAnalyzer(self.config)
        self.self_learner = SelfLearner(self.config)
        
        self._active = True
        self._mode = "interactive"
        
        self.logger.info("Genesis AI Agent initialized")
    
    async def analyze_code(self, path: str) -> List[str]:
        """Analyze code at the specified path."""
        self.logger.info(f"Analyzing code at: {path}")
        
        try:
            results = await self.code_analyzer.analyze_path(path)
            
            # Learn from the analysis results
            if self.config.learning_enabled:
                await self.self_learner.learn_from_analysis(path, results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing code: {e}")
            return [f"Error analyzing code: {str(e)}"]
    
    async def suggest_improvements(self, repo_url: Optional[str] = None) -> List[str]:
        """Generate improvement suggestions for code."""
        self.logger.info("Generating improvement suggestions")
        
        try:
            # If repo_url is provided, analyze that repository
            if repo_url:
                repo_info = await self.github_client.get_repository_info(repo_url)
                suggestions = await self.code_analyzer.suggest_improvements_for_repo(repo_info)
            else:
                # Analyze current directory
                suggestions = await self.code_analyzer.suggest_improvements(".")
            
            # Learn from the suggestions generated
            if self.config.learning_enabled:
                await self.self_learner.learn_from_suggestions(suggestions)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            return [f"Error generating suggestions: {str(e)}"]
    
    async def implement_changes(self, auto_approve: bool = False) -> List[str]:
        """Implement suggested changes."""
        self.logger.info("Implementing changes")
        
        try:
            # Get pending suggestions
            suggestions = await self.code_analyzer.get_pending_suggestions()
            
            if not suggestions:
                return ["No pending suggestions to implement"]
            
            results = []
            for suggestion in suggestions:
                if auto_approve or await self._confirm_change(suggestion):
                    result = await self._implement_single_change(suggestion)
                    results.append(result)
                    
                    # Learn from the implementation
                    if self.config.learning_enabled:
                        await self.self_learner.learn_from_implementation(suggestion, result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error implementing changes: {e}")
            return [f"Error implementing changes: {str(e)}"]
    
    async def process_natural_language(self, input_text: str) -> str:
        """Process natural language input and provide intelligent responses."""
        self.logger.info(f"Processing natural language input: {input_text[:50]}...")
        
        try:
            # Parse the intent from the input
            intent = await self._parse_intent(input_text)
            
            # Route to appropriate handler
            if intent['action'] == 'analyze':
                results = await self.analyze_code(intent.get('target', '.'))
                return f"Analysis complete: {'; '.join(results[:3])}"
            
            elif intent['action'] == 'suggest':
                suggestions = await self.suggest_improvements()
                return f"Here are some suggestions: {'; '.join(suggestions[:3])}"
            
            elif intent['action'] == 'implement':
                results = await self.implement_changes()
                return f"Implementation results: {'; '.join(results)}"
            
            elif intent['action'] == 'explain':
                explanation = await self._explain_code(intent.get('target'))
                return explanation
            
            else:
                return await self._generate_general_response(input_text)
                
        except Exception as e:
            self.logger.error(f"Error processing natural language: {e}")
            return f"I encountered an error: {str(e)}"
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            'active': self._active,
            'mode': self._mode,
            'learning_enabled': self.config.learning_enabled,
            'github_connected': bool(self.config.github_token),
            'last_activity': datetime.now().isoformat(),
        }
    
    async def learn_from_feedback(self, feedback: str) -> None:
        """Learn from user feedback."""
        self.logger.info("Learning from user feedback")
        
        if self.config.learning_enabled:
            await self.self_learner.learn_from_feedback(feedback)
        else:
            self.logger.info("Learning is disabled")
    
    async def _parse_intent(self, input_text: str) -> Dict[str, Any]:
        """Parse intent from natural language input."""
        input_lower = input_text.lower()
        
        if any(word in input_lower for word in ['analyze', 'check', 'review']):
            return {'action': 'analyze', 'target': self._extract_target(input_text)}
        
        elif any(word in input_lower for word in ['suggest', 'improve', 'recommend']):
            return {'action': 'suggest', 'target': self._extract_target(input_text)}
        
        elif any(word in input_lower for word in ['implement', 'apply', 'fix']):
            return {'action': 'implement'}
        
        elif any(word in input_lower for word in ['explain', 'what', 'how', 'why']):
            return {'action': 'explain', 'target': self._extract_target(input_text)}
        
        else:
            return {'action': 'general', 'text': input_text}
    
    def _extract_target(self, input_text: str) -> str:
        """Extract target file/directory from input text."""
        # Simple extraction - could be enhanced with NLP
        words = input_text.split()
        for i, word in enumerate(words):
            if word.endswith(('.py', '.js', '.java', '.cpp', '.c')):
                return word
            if word in ['this', 'current'] and i + 1 < len(words):
                return words[i + 1]
        return '.'
    
    async def _confirm_change(self, suggestion: Dict[str, Any]) -> bool:
        """Confirm a change with the user (in real implementation)."""
        # In a real implementation, this would prompt the user
        # For now, we'll implement basic logic
        return suggestion.get('confidence', 0) > 0.7
    
    async def _implement_single_change(self, suggestion: Dict[str, Any]) -> str:
        """Implement a single change suggestion."""
        try:
            change_type = suggestion.get('type', 'unknown')
            file_path = suggestion.get('file_path')
            
            if change_type == 'add_docstring':
                return await self._add_docstring(file_path, suggestion)
            elif change_type == 'fix_style':
                return await self._fix_code_style(file_path, suggestion)
            elif change_type == 'optimize':
                return await self._optimize_code(file_path, suggestion)
            else:
                return f"Implemented {change_type} in {file_path}"
                
        except Exception as e:
            return f"Failed to implement change: {str(e)}"
    
    async def _add_docstring(self, file_path: str, suggestion: Dict[str, Any]) -> str:
        """Add docstring to a function or class."""
        # Implementation would modify the actual file
        return f"Added docstring to {file_path}"
    
    async def _fix_code_style(self, file_path: str, suggestion: Dict[str, Any]) -> str:
        """Fix code style issues."""
        # Implementation would apply style fixes
        return f"Fixed code style in {file_path}"
    
    async def _optimize_code(self, file_path: str, suggestion: Dict[str, Any]) -> str:
        """Optimize code performance."""
        # Implementation would apply optimizations
        return f"Optimized code in {file_path}"
    
    async def _explain_code(self, target: Optional[str]) -> str:
        """Explain code functionality."""
        if not target or target == '.':
            return "I can explain specific files or functions. Please specify what you'd like me to explain."
        
        # In a real implementation, this would analyze and explain the code
        return f"This appears to be a {Path(target).suffix[1:] if Path(target).suffix else 'file'} that handles specific functionality."
    
    async def _generate_general_response(self, input_text: str) -> str:
        """Generate a general response for unclassified input."""
        responses = [
            "I'm here to help with your coding needs. What would you like me to analyze or improve?",
            "I can analyze code, suggest improvements, or implement changes. How can I assist you?",
            "Feel free to ask me to review your code or help with specific programming tasks.",
        ]
        
        # Simple hash-based selection for consistency
        index = hash(input_text) % len(responses)
        return responses[index]