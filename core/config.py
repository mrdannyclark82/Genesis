"""Configuration management for Genesis AI Agent."""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Configuration class for Genesis AI Agent."""
    
    # GitHub Configuration
    github_token: Optional[str] = None
    github_repo_owner: Optional[str] = None
    github_repo_name: Optional[str] = None
    
    # AI API Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Application Settings
    log_level: str = "INFO"
    debug: bool = False
    
    # Self-improvement Settings
    learning_enabled: bool = True
    feedback_storage_path: str = "./data/feedback.json"
    model_weights_path: str = "./data/model_weights.pkl"
    
    # External search settings
    serp_api_key: Optional[str] = None
    
    # Persona settings
    default_persona: str = "senior_developer"
    
    # Feature suggestion settings  
    enable_external_search: bool = True
    max_search_results: int = 10
    
    # Additional settings
    extra_settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        return cls(
            github_token=os.getenv('GITHUB_TOKEN'),
            github_repo_owner=os.getenv('GITHUB_REPO_OWNER'),
            github_repo_name=os.getenv('GITHUB_REPO_NAME'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            learning_enabled=os.getenv('LEARNING_ENABLED', 'True').lower() == 'true',
            feedback_storage_path=os.getenv('FEEDBACK_STORAGE_PATH', './data/feedback.json'),
            model_weights_path=os.getenv('MODEL_WEIGHTS_PATH', './data/model_weights.pkl'),
            serp_api_key=os.getenv('SERP_API_KEY'),
            default_persona=os.getenv('DEFAULT_PERSONA', 'senior_developer'),
            enable_external_search=os.getenv('ENABLE_EXTERNAL_SEARCH', 'True').lower() == 'true',
            max_search_results=int(os.getenv('MAX_SEARCH_RESULTS', '10')),
        )
    
    def validate(self) -> None:
        """Validate the configuration."""
        # Make GitHub token optional - warn instead of error
        if not self.github_token:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("GITHUB_TOKEN not set - some features may have limited functionality")
        
        # Create data directories if they don't exist
        feedback_dir = Path(self.feedback_storage_path).parent
        feedback_dir.mkdir(parents=True, exist_ok=True)
        
        weights_dir = Path(self.model_weights_path).parent
        weights_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self, key, self.extra_settings.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extra_settings[key] = value