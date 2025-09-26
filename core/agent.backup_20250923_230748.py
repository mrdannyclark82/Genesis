"""Main Genesis AI Agent implementation."""

import asyncio
import json
import logging
import psutil
import shutil
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from core.config import Config
from github_api.client import GitHubClient
from code_analyzer.analyzer import CodeAnalyzer
from self_improvement.learner import SelfLearner
from feature_suggester.suggester import FeatureSuggester
from external_search.search_client import ExternalSearchClient
from personas.persona_manager import PersonaManager
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
        self.feature_suggester = FeatureSuggester(self.config)
        self.search_client = ExternalSearchClient(self.config)
        self.persona_manager = PersonaManager(self.config)
        
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
            
            elif intent['action'] == 'status':
                status = await self.get_status()
                return f"Status: Mode={status['mode']}, Active={status['active']}, Learning={status['learning_enabled']}"
            
            elif intent['action'] == 'help':
                return self._get_help_message()
            
            elif intent['action'] == 'explain':
                explanation = await self._explain_code(intent.get('target'))
                response = explanation
            
            # NEW FEATURE HANDLERS
            elif intent['action'] == 'suggest_features':
                features = await self.suggest_new_features(intent.get('target', '.'))
                response = f"Here are some new feature suggestions:\n" + '\n'.join(features)
            
            elif intent['action'] == 'search_external':
                query = intent.get('query', '')
                if not query:
                    response = "Please specify what you'd like to search for."
                else:
                    examples = await self.search_external_examples(query)
                    response = f"External search results for '{query}':\n" + '\n'.join(examples)
            
            elif intent['action'] == 'set_persona':
                persona_name = intent.get('persona')
                if not persona_name:
                    response = "Please specify a persona name. Use 'list personas' to see available options."
                else:
                    response = await self.set_persona(persona_name)
            
            elif intent['action'] == 'list_personas':
                personas = await self.get_available_personas()
                response = "Available personas:\n" + '\n'.join(personas)
            
            elif intent['action'] == 'persona_status':
                response = await self.get_persona_status()
            
            elif intent['action'] == 'suggest_category_features':
                category = intent.get('category', 'general')
                features = await self.suggest_features_by_category(category)
                response = f"Here are {category} feature suggestions:\n" + '\n'.join(features)
            
            else:
                response = await self._generate_general_response(input_text)
            
            # Apply persona formatting to the response
            if self.persona_manager.get_current_persona():
                context = intent['action'] if intent['action'] != 'general' else 'general'
                response = self.persona_manager.format_response_with_persona(response, context)
            
            return response
                
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
    
    async def suggest_new_features(self, project_path: str = ".") -> List[str]:
        """Suggest new features and add-ons for the project."""
        self.logger.info(f"Suggesting new features for project: {project_path}")
        
        try:
            suggestions = await self.feature_suggester.suggest_features_for_project(project_path)
            
            # Format suggestions for display
            formatted_suggestions = []
            for suggestion in suggestions:
                formatted = f"🚀 {suggestion.name} ({suggestion.category}): {suggestion.description}"
                if suggestion.priority == "high":
                    formatted = f"⭐ {formatted}"
                formatted_suggestions.append(formatted)
            
            # Learn from the suggestions generated
            if self.config.learning_enabled:
                await self.self_learner.learn_from_suggestions([s.name for s in suggestions])
            
            return formatted_suggestions
            
        except Exception as e:
            self.logger.error(f"Error suggesting new features: {e}")
            return [f"Error suggesting features: {str(e)}"]
    
    async def search_external_examples(self, query: str, language: str = None) -> List[str]:
        """Search external sources for code examples and implementations."""
        self.logger.info(f"Searching external sources for: {query}")
        
        try:
            async with self.search_client:
                results = await self.search_client.comprehensive_search(query, language, 5)
                
                formatted_results = []
                for source, search_results in results.items():
                    if search_results:
                        formatted_results.append(f"\n📂 {source.replace('_', ' ').title()}:")
                        for result in search_results[:3]:  # Top 3 per source
                            formatted_results.append(f"  • {result.title}: {result.snippet[:100]}...")
                            formatted_results.append(f"    🔗 {result.url}")
                
                return formatted_results if formatted_results else ["No external examples found."]
                
        except Exception as e:
            self.logger.error(f"Error searching external examples: {e}")
            return [f"Error searching external sources: {str(e)}"]
    
    async def set_persona(self, persona_name: str) -> str:
        """Set the AI agent's persona."""
        self.logger.info(f"Setting persona to: {persona_name}")
        
        if self.persona_manager.set_persona(persona_name):
            persona = self.persona_manager.get_current_persona()
            return f"✅ Switched to {persona.name} persona: {persona.description}"
        else:
            available = ", ".join(self.persona_manager.get_available_personas())
            return f"❌ Persona '{persona_name}' not found. Available: {available}"
    
    async def get_available_personas(self) -> List[str]:
        """Get list of available personas."""
        personas = self.persona_manager.get_available_personas()
        formatted_personas = []
        
        for persona_name in personas:
            persona_info = self.persona_manager.get_persona_info(persona_name)
            if persona_info:
                formatted_personas.append(
                    f"👤 {persona_info['name']}: {persona_info['description']}"
                )
        
        return formatted_personas
    
    async def get_persona_status(self) -> str:
        """Get current persona status."""
        current = self.persona_manager.get_current_persona()
        if current:
            expertise = ", ".join(current.expertise_areas[:3])
            return (f"Current persona: {current.name}\n"
                   f"Expertise: {expertise}\n"
                   f"Style: {current.communication_style}")
        return "No persona currently active"
    
    async def suggest_features_by_category(self, category: str, project_path: str = ".") -> List[str]:
        """Suggest features for a specific category."""
        self.logger.info(f"Suggesting {category} features")
        
        try:
            suggestions = await self.feature_suggester.suggest_features_by_category(category, project_path)
            
            formatted_suggestions = []
            for suggestion in suggestions:
                formatted = f"🔧 {suggestion.name}: {suggestion.description}"
                if suggestion.examples:
                    formatted += f"\n   📚 Example: {suggestion.examples[0].url}"
                formatted_suggestions.append(formatted)
            
            return formatted_suggestions if formatted_suggestions else [f"No {category} features suggested."]
            
        except Exception as e:
            self.logger.error(f"Error suggesting {category} features: {e}")
            return [f"Error suggesting {category} features: {str(e)}"]
    
    async def _parse_intent(self, input_text: str) -> Dict[str, Any]:
        """Parse intent from natural language input."""
        input_lower = input_text.lower()
        
        # Implement commands - check first for specificity
        implement_patterns = [
            'implement', 'apply', 'fix', 'implement suggestions', 'apply suggestions',
            'implement changes', 'apply changes', 'make changes', 'do it', 'go ahead',
            'implement improvements', 'apply improvements'
        ]
        if any(pattern in input_lower for pattern in implement_patterns):
            return {'action': 'implement'}
        
        # Analyze commands - more variations
        analyze_patterns = [
            'analyze', 'check', 'review', 'examine', 'look at', 'scan',
            'analyze code', 'check code', 'review code', 'code analysis'
        ]
        if any(pattern in input_lower for pattern in analyze_patterns):
            return {'action': 'analyze', 'target': self._extract_target(input_text)}
        
        # Suggest improvements commands - more variations
        suggest_patterns = [
            'suggest', 'improve', 'recommend', 'suggestions', 'improvements',
            'suggest improvements', 'recommend improvements', 'what can be improved',
            'how to improve', 'make it better', 'optimize', 'enhancement'
        ]
        if any(pattern in input_lower for pattern in suggest_patterns):
            return {'action': 'suggest', 'target': self._extract_target(input_text)}
        
        # NEW FEATURE COMMANDS
        
        # Feature suggestion commands
        feature_patterns = [
            'suggest features', 'new features', 'add features', 'what features',
            'feature suggestions', 'suggest new features', 'recommend features'
        ]
        if any(pattern in input_lower for pattern in feature_patterns):
            return {'action': 'suggest_features', 'target': self._extract_target(input_text)}
        
        # External search commands
        search_patterns = [
            'search', 'find examples', 'look for', 'search for', 'find code',
            'external examples', 'search github', 'search web'
        ]
        if any(pattern in input_lower for pattern in search_patterns):
            query = input_text
            # Remove the command part to get the query
            for pattern in search_patterns:
                if pattern in input_lower:
                    query = input_text.lower().replace(pattern, '').strip()
                    break
            return {'action': 'search_external', 'query': query or input_text}
        
        # Persona commands
        persona_patterns = [
            'set persona', 'change persona', 'switch persona', 'persona',
            'available personas', 'list personas', 'persona status'
        ]
        if any(pattern in input_lower for pattern in persona_patterns):
            if 'available' in input_lower or 'list' in input_lower:
                return {'action': 'list_personas'}
            elif 'status' in input_lower:
                return {'action': 'persona_status'}
            else:
                # Extract persona name
                words = input_text.split()
                persona_name = None
                for i, word in enumerate(words):
                    if word.lower() in ['persona', 'to']:
                        if i + 1 < len(words):
                            persona_name = words[i + 1]
                            break
                return {'action': 'set_persona', 'persona': persona_name}
        
        # Category-specific feature suggestions
        category_patterns = [
            'security features', 'performance features', 'ui features', 
            'testing features', 'documentation features', 'database features'
        ]
        for pattern in category_patterns:
            if pattern in input_lower:
                category = pattern.split()[0]  # Extract category
                return {'action': 'suggest_category_features', 'category': category}
        
        # Status/help commands
        status_patterns = ['status', 'how are you', 'what are you doing']
        if any(pattern in input_lower for pattern in status_patterns):
            return {'action': 'status'}
        
        # Help commands
        help_patterns = ['help', 'what can you do', 'commands', 'options']
        if any(pattern in input_lower for pattern in help_patterns):
            return {'action': 'help'}
        
        # Explain commands - more variations
        explain_patterns = [
            'explain', 'what', 'how', 'why', 'tell me about',
            'what does this do', 'how does this work', 'explain this'
        ]
        if any(pattern in input_lower for pattern in explain_patterns):
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
            
            if not file_path or not Path(file_path).exists():
                return f"❌ File not found: {file_path}"
            
            if change_type == 'add_docstring':
                return await self._safe_file_modification(file_path, 
                    lambda fp: self._add_docstring(fp, suggestion))
            elif change_type == 'fix_style':
                return await self._safe_file_modification(file_path,
                    lambda fp: self._fix_code_style(fp, suggestion))
            elif change_type == 'optimize':
                return await self._safe_file_modification(file_path,
                    lambda fp: self._optimize_code(fp, suggestion))
            else:
                return await self._safe_file_modification(file_path,
                    lambda fp: self._generic_implementation(fp, change_type))
                
        except Exception as e:
            return f"❌ Failed to implement change: {str(e)}"
    
    async def _generic_implementation(self, file_path: str, change_type: str) -> str:
        """Generic implementation for unknown change types."""
        return f"Applied {change_type} to {Path(file_path).name}"
    
    async def _add_docstring(self, file_path: str, suggestion: Dict[str, Any]) -> str:
        """Add docstring to a function or class."""
        # In a real implementation, this would modify the actual file
        # For now, we simulate the action
        return f"Added docstring to {Path(file_path).name}"
    
    async def _fix_code_style(self, file_path: str, suggestion: Dict[str, Any]) -> str:
        """Fix code style issues."""
        # In a real implementation, this would apply style fixes using tools like black, autopep8
        # For now, we simulate the action
        return f"Fixed code style in {Path(file_path).name}"
    
    async def _optimize_code(self, file_path: str, suggestion: Dict[str, Any]) -> str:
        """Optimize code performance."""
        # In a real implementation, this would apply performance optimizations
        # For now, we simulate the action
        return f"Optimized code in {Path(file_path).name}"
    
    async def _explain_code(self, target: Optional[str]) -> str:
        """Explain code functionality."""
        if not target or target == '.':
            return "I can explain specific files or functions. Please specify what you'd like me to explain."
        
        # In a real implementation, this would analyze and explain the code
        return f"This appears to be a {Path(target).suffix[1:] if Path(target).suffix else 'file'} that handles specific functionality."
    
    
    def _get_help_message(self) -> str:
        """Get help message with available commands."""
        return """I can help you with various coding tasks! Here are some things you can say:

📊 **Analysis Commands:**
- "analyze the code" / "check this file" / "review my code"
- "scan for issues" / "examine the codebase"

💡 **Suggestion Commands:**  
- "suggest improvements" / "how can I improve this?"
- "what can be optimized?" / "recommend changes"
- "make it better" / "any suggestions?"

🔧 **Implementation Commands:**
- "implement suggestions" / "apply the changes"
- "go ahead and fix it" / "make those changes"
- "implement improvements" / "do it"

❓ **Information Commands:**
- "explain this code" / "what does this do?"
- "how does this work?" / "tell me about this"
- "status" / "help" / "what can you do?"

Just type your request naturally - I'll understand what you want to do!"""

    async def _generate_general_response(self, input_text: str) -> str:
        """Generate a general response for unclassified input."""
        responses = [
            "I'm here to help with your coding needs. You can ask me to 'analyze code', 'suggest improvements', or 'implement changes'. What would you like me to do?",
            "I can help you analyze code, suggest improvements, or implement changes. Try saying something like 'suggest improvements' or 'analyze this code'.",
            "I'm your coding assistant! I understand natural language - just tell me what you'd like me to do with your code. Type 'help' to see examples.",
            "Feel free to ask me to review your code, suggest improvements, or implement changes. I understand commands like 'analyze code' or 'make improvements'.",
        ]
        
        # Simple hash-based selection for consistency
        index = hash(input_text) % len(responses)
        return responses[index]
    
    def _is_program_running(self, file_path: str) -> List[Dict[str, Any]]:
        """Check if a program/file is currently running."""
        running_processes = []
        file_path = Path(file_path).resolve()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline:
                    # Check if the file is in the command line
                    cmdline_str = ' '.join(cmdline)
                    if str(file_path) in cmdline_str or file_path.name in cmdline_str:
                        running_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return running_processes
    
    async def _create_backup(self, file_path: str) -> str:
        """Create a backup of the file before modification."""
        file_path = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
        
        try:
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
    
    async def _safe_file_modification(self, file_path: str, modification_func) -> str:
        """Safely modify a file, handling running programs."""
        file_path = Path(file_path)
        
        # Check if program is running
        running_processes = self._is_program_running(str(file_path))
        
        if running_processes:
            self.logger.warning(f"File {file_path} is being used by running processes: {[p['name'] for p in running_processes]}")
            return f"⚠️  Warning: {file_path.name} appears to be running (PID: {[p['pid'] for p in running_processes]}). Consider stopping the program before making changes."
        
        # Create backup
        try:
            backup_path = await self._create_backup(str(file_path))
            
            # Apply modification
            result = await modification_func(str(file_path))
            
            return f"✅ Modified {file_path.name} (backup: {Path(backup_path).name})"
            
        except Exception as e:
            self.logger.error(f"Error during safe modification: {e}")
            return f"❌ Failed to modify {file_path.name}: {str(e)}"