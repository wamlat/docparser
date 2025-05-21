from dotenv import load_dotenv, set_key
import os
import re

# Check if .env file exists
env_path = ".env"
if not os.path.exists(env_path):
    print(f"ERROR: {env_path} file not found. Creating a default one.")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("""# OpenAI API Key for LLM Fallback Parser
OPENAI_API_KEY=your_openai_api_key_here

# Set to true to always use LLM parser instead of NER+regex
USE_LLM_PARSER=true

# Set confidence threshold for LLM fallback (default is 0.6)
CONFIDENCE_THRESHOLD=0.6

# LLM Model Configuration
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1000
LLM_BASE_CONFIDENCE=0.8
""")

# Load environment variables from .env file
print("Loading .env file...")
load_dotenv(override=True)

# Check if OPENAI_API_KEY is set and valid
api_key = os.environ.get('OPENAI_API_KEY', '')
if not api_key or api_key == 'your_openai_api_key_here':
    print("\n⚠️ WARNING: OpenAI API key is not set properly.")
    new_key = input("Enter your OpenAI API key (or leave blank to skip): ").strip()
    if new_key:
        set_key(env_path, 'OPENAI_API_KEY', new_key)
        api_key = new_key
        os.environ['OPENAI_API_KEY'] = new_key
        print("✅ API key updated in .env file.")
else:
    # Check if key matches expected format (sk-...)
    if not re.match(r'^sk-[A-Za-z0-9]{48}$', api_key):
        print("\n⚠️ WARNING: API key does not have the expected format (should start with 'sk-' followed by 48 characters).")
        if input("Would you like to update it? (y/n): ").lower() == 'y':
            new_key = input("Enter your OpenAI API key: ").strip()
            if new_key:
                set_key(env_path, 'OPENAI_API_KEY', new_key)
                api_key = new_key
                os.environ['OPENAI_API_KEY'] = new_key
                print("✅ API key updated in .env file.")
    else:
        print("✅ API key format looks valid.")

# Check USE_LLM_PARSER flag
use_llm = os.environ.get('USE_LLM_PARSER', '').lower() in ('true', '1', 'yes')
if not use_llm:
    print("\n⚠️ LLM parser is not enabled.")
    if input("Would you like to enable it? (y/n): ").lower() == 'y':
        set_key(env_path, 'USE_LLM_PARSER', 'true')
        os.environ['USE_LLM_PARSER'] = 'true'
        print("✅ LLM parser enabled in .env file.")
else:
    print("✅ LLM parser is enabled.")

# Output current environment settings
print("\n==== Current Environment Settings ====")
print(f"OPENAI_API_KEY: {'*' * 8 + api_key[-4:] if len(api_key) > 4 else 'Not set properly'}")
print(f"USE_LLM_PARSER: {os.environ.get('USE_LLM_PARSER', 'Not set')}")
print(f"CONFIDENCE_THRESHOLD: {os.environ.get('CONFIDENCE_THRESHOLD', 'Not set')}")
print(f"LLM_MODEL: {os.environ.get('LLM_MODEL', 'Not set')}")
print(f"LLM_TEMPERATURE: {os.environ.get('LLM_TEMPERATURE', 'Not set')}")
print(f"LLM_MAX_TOKENS: {os.environ.get('LLM_MAX_TOKENS', 'Not set')}")
print(f"LLM_BASE_CONFIDENCE: {os.environ.get('LLM_BASE_CONFIDENCE', 'Not set')}")

print("\nChanges have been applied. Please restart the application for them to take effect.")

def check_environment_variables():
    # Check if environment variables are set
    print("Checking environment variables...")
    print(f"OPENAI_API_KEY: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Not set'}")
    print(f"USE_LLM_PARSER: {os.environ.get('USE_LLM_PARSER', 'Not set')}")
    print(f"LLM_MODEL: {os.environ.get('LLM_MODEL', 'Not set')}")
    print(f"LLM_TEMPERATURE: {os.environ.get('LLM_TEMPERATURE', 'Not set')}")
    print(f"LLM_MAX_TOKENS: {os.environ.get('LLM_MAX_TOKENS', 'Not set')}")
    print(f"LLM_BASE_CONFIDENCE: {os.environ.get('LLM_BASE_CONFIDENCE', 'Not set')}")
    print(f"CONFIDENCE_THRESHOLD: {os.environ.get('CONFIDENCE_THRESHOLD', 'Not set')}") 