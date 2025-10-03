"""LLM client for interacting with AI models via OpenRouter."""

import os
import json
import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from core.config import Config
from utils.logger import get_logger


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class LLMClient:
    """Client for interacting with LLM models via OpenRouter API."""
    
    def __init__(self, config: Config):
        """Initialize the LLM client."""
        self.config = config
        self.logger = get_logger(__name__)
        self.api_key = config.openrouter_api_key
        self.model = config.llm_model
        self.base_url = "https://openrouter.ai/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            self.logger.warning("OpenRouter API key not set - LLM features will be unavailable")
        
        self.logger.info(f"LLM client initialized with model: {self.model}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """
        Send a chat completion request to the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt to prepend
            
        Returns:
            LLMResponse object or None if request fails
        """
        if not self.api_key:
            self.logger.error("OpenRouter API key not configured")
            return None
        
        try:
            # Prepend system prompt if provided
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            # Ensure session exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/mrdannyclark82/Genesis",
                "X-Title": "Genesis AI Agent"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            self.logger.debug(f"Sending request to OpenRouter with model: {self.model}")
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    return None
                
                data = await response.json()
                
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content", "")
                
                return LLMResponse(
                    content=content,
                    model=data.get("model", self.model),
                    usage=data.get("usage", {}),
                    finish_reason=choice.get("finish_reason", "unknown")
                )
                
        except Exception as e:
            self.logger.error(f"Error making LLM request: {e}")
            return None
    
    async def generate_code_analysis(self, code: str, language: str = "python") -> Optional[str]:
        """
        Generate code analysis using LLM.
        
        Args:
            code: Source code to analyze
            language: Programming language
            
        Returns:
            Analysis text or None
        """
        system_prompt = f"""You are an expert {language} code reviewer and software architect. 
Analyze the provided code and provide detailed, actionable feedback on:
- Code quality and best practices
- Potential bugs or issues
- Performance optimizations
- Security concerns
- Suggestions for improvement"""
        
        messages = [
            {"role": "user", "content": f"Analyze this {language} code:\n\n```{language}\n{code}\n```"}
        ]
        
        response = await self.chat_completion(messages, system_prompt=system_prompt, max_tokens=1500)
        return response.content if response else None
    
    async def generate_improvement_suggestions(self, project_description: str) -> Optional[str]:
        """
        Generate improvement suggestions for a project.
        
        Args:
            project_description: Description of the project
            
        Returns:
            Suggestions text or None
        """
        system_prompt = """You are a senior software engineer and architect. 
Suggest concrete, actionable improvements for software projects. 
Focus on practical enhancements that add real value."""
        
        messages = [
            {"role": "user", "content": f"Suggest improvements for this project:\n\n{project_description}"}
        ]
        
        response = await self.chat_completion(messages, system_prompt=system_prompt, max_tokens=1500)
        return response.content if response else None
    
    async def answer_question(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """
        Answer a question with optional context.
        
        Args:
            question: The question to answer
            context: Optional context to help answer
            
        Returns:
            Answer text or None
        """
        system_prompt = """You are a helpful AI coding assistant. 
Provide clear, concise, and accurate answers to programming questions.
Focus on practical solutions and best practices."""
        
        user_content = question
        if context:
            user_content = f"Context:\n{context}\n\nQuestion: {question}"
        
        messages = [
            {"role": "user", "content": user_content}
        ]
        
        response = await self.chat_completion(messages, system_prompt=system_prompt)
        return response.content if response else None
    
    async def generate_feature_suggestions(self, project_info: str) -> Optional[str]:
        """
        Generate feature suggestions based on project information.
        
        Args:
            project_info: Information about the project
            
        Returns:
            Feature suggestions or None
        """
        system_prompt = """You are a product manager and software architect.
Suggest innovative, practical features that would enhance the project.
Consider user needs, technical feasibility, and industry trends."""
        
        messages = [
            {"role": "user", "content": f"Based on this project information, suggest new features:\n\n{project_info}"}
        ]
        
        response = await self.chat_completion(messages, system_prompt=system_prompt, max_tokens=1500)
        return response.content if response else None
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None
