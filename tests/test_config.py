"""Tests for configuration module."""

import os
import tempfile
from pathlib import Path

import pytest

from core.config import Config


def test_config_from_env():
    """Test creating config from environment variables."""
    # Set environment variables
    os.environ['GITHUB_TOKEN'] = 'test_token'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    config = Config.from_env()
    
    assert config.github_token == 'test_token'
    assert config.log_level == 'DEBUG'
    
    # Clean up
    del os.environ['GITHUB_TOKEN']
    del os.environ['LOG_LEVEL']


def test_config_validation():
    """Test config validation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config(
            github_token='test_token',
            feedback_storage_path=f'{temp_dir}/feedback.json',
            model_weights_path=f'{temp_dir}/weights.pkl'
        )
        
        # Should not raise exception
        config.validate()
        
        # Check directories were created
        assert Path(f'{temp_dir}/feedback.json').parent.exists()
        assert Path(f'{temp_dir}/weights.pkl').parent.exists()


def test_config_validation_missing_token():
    """Test config validation with missing token."""
    config = Config()
    
    with pytest.raises(ValueError, match="GITHUB_TOKEN is required"):
        config.validate()


def test_config_get_set():
    """Test getting and setting config values."""
    config = Config()
    
    # Test getting existing attribute
    assert config.get('log_level') == 'INFO'
    
    # Test getting non-existing attribute with default
    assert config.get('non_existing', 'default') == 'default'
    
    # Test setting existing attribute
    config.set('log_level', 'DEBUG')
    assert config.log_level == 'DEBUG'
    
    # Test setting new attribute
    config.set('new_setting', 'value')
    assert config.get('new_setting') == 'value'