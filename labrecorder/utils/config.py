"""
Configuration handling for Lab Recorder.
"""

import json
import os
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for Lab Recorder."""
    
    DEFAULT_CONFIG = {
        'filename': 'recording.xdf',
        'remote_control': {
            'enabled': True,
            'port': 22345
        },
        'recording': {
            'buffer_size': 360,
            'max_samples_per_pull': 500,
            'clock_sync_interval': 5.0
        },
        'streams': {
            'timeout': 2.0,
            'recover': True
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = config_file
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, filename: str) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            filename: Path to configuration file
        """
        try:
            with open(filename, 'r') as f:
                file_config = json.load(f)
                self._deep_update(self.config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {filename}: {e}")
    
    def save_to_file(self, filename: str) -> None:
        """
        Save current configuration to JSON file.
        
        Args:
            filename: Path to save configuration file
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config file {filename}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'remote_control.port')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final key
        config[keys[-1]] = value
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """
        Deep update of nested dictionaries.
        
        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with updates
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value 