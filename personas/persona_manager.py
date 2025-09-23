"""Persona management system for different interaction styles and expertise areas."""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from core.config import Config
from utils.logger import get_logger


@dataclass
class Persona:
    """Represents a persona with specific characteristics and behavior patterns."""
    name: str
    description: str
    expertise_areas: List[str]
    communication_style: str
    response_templates: Dict[str, str]
    suggested_actions: List[str]
    personality_traits: List[str]
    preferred_technologies: List[str]
    focus_areas: List[str]
    example_responses: Dict[str, str]


class PersonaManager:
    """Manages different personas for the AI agent."""
    
    def __init__(self, config: Config):
        """Initialize the persona manager."""
        self.config = config
        self.logger = get_logger(__name__)
        self.current_persona: Optional[Persona] = None
        self.available_personas: Dict[str, Persona] = {}
        
        # Load predefined personas
        self._load_predefined_personas()
        
        # Set default persona
        self.set_persona("senior_developer")
        
        self.logger.info("Persona manager initialized")
    
    def get_available_personas(self) -> List[str]:
        """Get list of available persona names."""
        return list(self.available_personas.keys())
    
    def get_persona_info(self, persona_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a persona."""
        persona = self.available_personas.get(persona_name)
        if persona:
            return asdict(persona)
        return None
    
    def set_persona(self, persona_name: str) -> bool:
        """Set the current active persona."""
        if persona_name in self.available_personas:
            self.current_persona = self.available_personas[persona_name]
            self.logger.info(f"Switched to persona: {persona_name}")
            return True
        else:
            self.logger.warning(f"Persona not found: {persona_name}")
            return False
    
    def get_current_persona(self) -> Optional[Persona]:
        """Get the current active persona."""
        return self.current_persona
    
    def format_response_with_persona(self, response: str, context: str = "general") -> str:
        """Format a response according to the current persona's style."""
        if not self.current_persona:
            return response
        
        persona = self.current_persona
        
        # Apply communication style
        if persona.communication_style == "formal":
            response = self._make_formal(response)
        elif persona.communication_style == "casual":
            response = self._make_casual(response)
        elif persona.communication_style == "technical":
            response = self._make_technical(response)
        elif persona.communication_style == "encouraging":
            response = self._make_encouraging(response)
        
        # Add persona-specific prefix if available
        if context in persona.response_templates:
            template = persona.response_templates[context]
            response = template.format(response=response)
        
        return response
    
    def get_persona_suggestions(self, context: str = "general") -> List[str]:
        """Get suggestions based on current persona's focus areas."""
        if not self.current_persona:
            return []
        
        suggestions = []
        persona = self.current_persona
        
        # Add persona-specific suggestions
        suggestions.extend(persona.suggested_actions)
        
        # Add focus area related suggestions
        for area in persona.focus_areas:
            if area == "security" and context in ["code_review", "suggestions"]:
                suggestions.append("Consider security implications and add input validation")
                suggestions.append("Review for potential vulnerabilities")
            elif area == "performance" and context in ["code_review", "suggestions"]:
                suggestions.append("Analyze performance bottlenecks")
                suggestions.append("Consider caching strategies")
            elif area == "testing" and context in ["code_review", "suggestions"]:
                suggestions.append("Add comprehensive test coverage")
                suggestions.append("Consider edge cases and error scenarios")
            elif area == "documentation" and context in ["code_review", "suggestions"]:
                suggestions.append("Improve code documentation and comments")
                suggestions.append("Add usage examples")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_expertise_match_score(self, topic: str) -> float:
        """Get how well the current persona matches a given topic."""
        if not self.current_persona:
            return 0.5
        
        topic_lower = topic.lower()
        score = 0.0
        
        # Check expertise areas
        for area in self.current_persona.expertise_areas:
            if area.lower() in topic_lower or topic_lower in area.lower():
                score += 0.3
        
        # Check preferred technologies
        for tech in self.current_persona.preferred_technologies:
            if tech.lower() in topic_lower:
                score += 0.2
        
        # Check focus areas
        for focus in self.current_persona.focus_areas:
            if focus.lower() in topic_lower:
                score += 0.1
        
        return min(score, 1.0)
    
    def suggest_persona_for_task(self, task_description: str) -> str:
        """Suggest the best persona for a specific task."""
        best_persona = "senior_developer"
        best_score = 0.0
        
        for persona_name, persona in self.available_personas.items():
            # Temporarily set persona to calculate score
            temp_current = self.current_persona
            self.current_persona = persona
            score = self.get_expertise_match_score(task_description)
            self.current_persona = temp_current
            
            if score > best_score:
                best_score = score
                best_persona = persona_name
        
        return best_persona
    
    def create_custom_persona(self, persona_data: Dict[str, Any]) -> bool:
        """Create a custom persona from provided data."""
        try:
            persona = Persona(
                name=persona_data['name'],
                description=persona_data.get('description', ''),
                expertise_areas=persona_data.get('expertise_areas', []),
                communication_style=persona_data.get('communication_style', 'professional'),
                response_templates=persona_data.get('response_templates', {}),
                suggested_actions=persona_data.get('suggested_actions', []),
                personality_traits=persona_data.get('personality_traits', []),
                preferred_technologies=persona_data.get('preferred_technologies', []),
                focus_areas=persona_data.get('focus_areas', []),
                example_responses=persona_data.get('example_responses', {})
            )
            
            self.available_personas[persona.name] = persona
            self.logger.info(f"Created custom persona: {persona.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating custom persona: {e}")
            return False
    
    def _load_predefined_personas(self):
        """Load predefined personas."""
        personas_data = {
            "senior_developer": {
                "name": "Senior Developer",
                "description": "Experienced software developer with focus on best practices and code quality",
                "expertise_areas": ["software_architecture", "code_review", "best_practices", "debugging"],
                "communication_style": "professional",
                "response_templates": {
                    "analysis": "Based on my analysis, {response}",
                    "suggestion": "I recommend the following approach: {response}",
                    "error": "I've identified the following issues: {response}"
                },
                "suggested_actions": [
                    "Review code for best practices",
                    "Suggest architectural improvements",
                    "Recommend testing strategies",
                    "Identify potential bugs"
                ],
                "personality_traits": ["methodical", "detail-oriented", "pragmatic"],
                "preferred_technologies": ["python", "javascript", "git", "docker"],
                "focus_areas": ["code_quality", "maintainability", "scalability"],
                "example_responses": {
                    "greeting": "Hello! I'm here to help you with your development challenges. Let's write some quality code together.",
                    "code_review": "I've reviewed your code and have some suggestions for improvement..."
                }
            },
            
            "security_expert": {
                "name": "Security Expert",
                "description": "Cybersecurity specialist focused on secure coding practices and vulnerability assessment",
                "expertise_areas": ["security_auditing", "vulnerability_assessment", "secure_coding", "penetration_testing"],
                "communication_style": "technical",
                "response_templates": {
                    "analysis": "From a security perspective: {response}",
                    "suggestion": "Security recommendation: {response}",
                    "warning": "⚠️ Security concern: {response}"
                },
                "suggested_actions": [
                    "Audit code for security vulnerabilities",
                    "Check input validation",
                    "Review authentication mechanisms",
                    "Assess data encryption"
                ],
                "personality_traits": ["cautious", "thorough", "security-focused"],
                "preferred_technologies": ["security_tools", "encryption", "authentication", "firewalls"],
                "focus_areas": ["security", "privacy", "compliance"],
                "example_responses": {
                    "greeting": "Security first! I'm here to help you identify and fix potential security vulnerabilities.",
                    "code_review": "I've found several security concerns that need immediate attention..."
                }
            },
            
            "ui_ux_specialist": {
                "name": "UI/UX Specialist",
                "description": "User interface and experience designer focused on usability and user-centered design",
                "expertise_areas": ["user_interface_design", "user_experience", "accessibility", "usability_testing"],
                "communication_style": "encouraging",
                "response_templates": {
                    "analysis": "From a user experience standpoint: {response}",
                    "suggestion": "To improve user experience: {response}",
                    "feedback": "User feedback: {response}"
                },
                "suggested_actions": [
                    "Improve user interface design",
                    "Enhance user experience flow",
                    "Check accessibility compliance",
                    "Optimize for mobile devices"
                ],
                "personality_traits": ["user-focused", "creative", "empathetic"],
                "preferred_technologies": ["html", "css", "javascript", "design_tools"],
                "focus_areas": ["usability", "accessibility", "design"],
                "example_responses": {
                    "greeting": "Let's create amazing user experiences! I'm here to help make your application more user-friendly.",
                    "code_review": "I see opportunities to make this more intuitive for users..."
                }
            },
            
            "performance_optimizer": {
                "name": "Performance Optimizer",
                "description": "Specialist in application performance optimization and scalability",
                "expertise_areas": ["performance_optimization", "scalability", "caching", "database_optimization"],
                "communication_style": "technical",
                "response_templates": {
                    "analysis": "Performance analysis shows: {response}",
                    "suggestion": "Optimization opportunity: {response}",
                    "metrics": "Performance metrics: {response}"
                },
                "suggested_actions": [
                    "Analyze performance bottlenecks",
                    "Optimize database queries",
                    "Implement caching strategies",
                    "Review memory usage"
                ],
                "personality_traits": ["analytical", "efficiency-focused", "data-driven"],
                "preferred_technologies": ["profiling_tools", "databases", "caching", "monitoring"],
                "focus_areas": ["performance", "scalability", "efficiency"],
                "example_responses": {
                    "greeting": "Speed matters! Let's optimize your application for peak performance.",
                    "code_review": "I've identified several performance optimization opportunities..."
                }
            },
            
            "devops_engineer": {
                "name": "DevOps Engineer",
                "description": "Infrastructure and deployment specialist focused on CI/CD and automation",
                "expertise_areas": ["infrastructure", "deployment", "ci_cd", "automation", "monitoring"],
                "communication_style": "technical",
                "response_templates": {
                    "analysis": "Infrastructure analysis: {response}",
                    "suggestion": "DevOps recommendation: {response}",
                    "deployment": "Deployment strategy: {response}"
                },
                "suggested_actions": [
                    "Set up CI/CD pipelines",
                    "Containerize applications",
                    "Implement monitoring",
                    "Automate deployment processes"
                ],
                "personality_traits": ["automation-focused", "reliability-conscious", "systematic"],
                "preferred_technologies": ["docker", "kubernetes", "jenkins", "aws", "terraform"],
                "focus_areas": ["automation", "reliability", "deployment"],
                "example_responses": {
                    "greeting": "Let's automate and scale your infrastructure! I'm here to help with DevOps best practices.",
                    "code_review": "From an operations perspective, consider these improvements..."
                }
            },
            
            "junior_mentor": {
                "name": "Junior Developer Mentor",
                "description": "Patient mentor focused on teaching and guiding junior developers",
                "expertise_areas": ["mentoring", "teaching", "code_explanation", "learning_guidance"],
                "communication_style": "encouraging",
                "response_templates": {
                    "explanation": "Let me explain this step by step: {response}",
                    "suggestion": "Here's a learning opportunity: {response}",
                    "encouragement": "Great question! {response}"
                },
                "suggested_actions": [
                    "Explain coding concepts clearly",
                    "Provide learning resources",
                    "Suggest practice exercises",
                    "Encourage best practices"
                ],
                "personality_traits": ["patient", "encouraging", "educational"],
                "preferred_technologies": ["fundamentals", "tutorials", "documentation"],
                "focus_areas": ["learning", "fundamentals", "growth"],
                "example_responses": {
                    "greeting": "Welcome! I'm here to help you learn and grow as a developer. No question is too basic!",
                    "code_review": "This is a great start! Let me help you improve it further..."
                }
            }
        }
        
        # Create persona objects
        for persona_name, data in personas_data.items():
            persona = Persona(
                name=data["name"],
                description=data["description"],
                expertise_areas=data["expertise_areas"],
                communication_style=data["communication_style"],
                response_templates=data["response_templates"],
                suggested_actions=data["suggested_actions"],
                personality_traits=data["personality_traits"],
                preferred_technologies=data["preferred_technologies"],
                focus_areas=data["focus_areas"],
                example_responses=data["example_responses"]
            )
            self.available_personas[persona_name] = persona
    
    def _make_formal(self, response: str) -> str:
        """Make response more formal."""
        # Simple formal transformations
        response = response.replace("I think", "I believe")
        response = response.replace("you should", "I recommend that you")
        response = response.replace("can't", "cannot")
        response = response.replace("won't", "will not")
        return response
    
    def _make_casual(self, response: str) -> str:
        """Make response more casual."""
        # Simple casual transformations
        response = response.replace("I recommend", "I'd suggest")
        response = response.replace("You should consider", "You might want to")
        return response
    
    def _make_technical(self, response: str) -> str:
        """Make response more technical."""
        # Add technical emphasis
        if not response.startswith(("Technical", "From a technical")):
            response = f"Technical analysis: {response}"
        return response
    
    def _make_encouraging(self, response: str) -> str:
        """Make response more encouraging."""
        encouraging_prefixes = [
            "Great work! ", "Nice progress! ", "You're on the right track! ",
            "Excellent question! ", "That's a smart approach! "
        ]
        
        # Randomly add encouraging prefix (in practice, you might want more sophisticated logic)
        import random
        if random.random() < 0.3:  # 30% chance to add encouraging prefix
            prefix = random.choice(encouraging_prefixes)
            response = f"{prefix}{response}"
        
        return response