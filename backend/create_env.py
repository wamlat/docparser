#!/usr/bin/env python3
import os
import sys
from dotenv import set_key

def create_env_file():
    """Create a .env file with essential configuration."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Default settings
    defaults = {
        'OPENAI_API_KEY': 'your_openai_api_key_here',
        'USE_LLM_PARSER': 'true',
        'LLM_MODEL': 'gpt-3.5-turbo',
        'LLM_TEMPERATURE': '0.2',
        'LLM_MAX_TOKENS': '1000',
        'LLM_BASE_CONFIDENCE': '0.8',
        'CONFIDENCE_THRESHOLD': '0.6'
    }
    
    # Create file if it doesn't exist
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write("# DocParser Environment Configuration\n\n")
    
    # Update each setting
    for key, value in defaults.items():
        # Don't overwrite existing values
        if not os.environ.get(key):
            set_key(env_path, key, value)
            print(f"Set {key}={value}")
        else:
            print(f"Keeping existing {key}={os.environ.get(key)}")
    
    print(f"\nEnvironment file created at: {env_path}")
    print("Please edit this file to set your OpenAI API key.")

if __name__ == "__main__":
    create_env_file() 