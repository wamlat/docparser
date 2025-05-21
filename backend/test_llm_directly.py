"""
Test the LLM fallback parser directly.
"""
import os
import json
import sys
from dotenv import load_dotenv

# Make sure environment variables are loaded
load_dotenv()

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the parser functions
try:
    # First check if the environment is set up correctly
    api_key = os.environ.get('OPENAI_API_KEY', '')
    use_llm = os.environ.get('USE_LLM_PARSER', '').lower() in ('true', '1', 'yes')
    
    print(f"API key set: {bool(api_key and api_key != 'your_openai_api_key_here')}")
    print(f"USE_LLM_PARSER: {use_llm}")
    
    if not api_key or api_key == 'your_openai_api_key_here':
        print("ERROR: OpenAI API key is not set properly. Please run check_env.py first.")
        sys.exit(1)
    
    if not use_llm:
        print("WARNING: USE_LLM_PARSER is not enabled, but we'll test the parser directly anyway.")
    
    # Now import the necessary functions
    from app.llm_fallback import parse_with_llm
    
    # Define a sample order text
    sample_text = """
    ORDER CONFIRMATION
    Order #: PO-12345
    Date: 2023-05-15

    Ship to:
    Acme Corporation
    123 Main Street
    Suite 100
    San Francisco, CA 94105

    Line Items:
    1. HTP-2000 | Qty: 5 | $125.00 each
    2. LMN-300X | Qty: 2 | $45.50 each
    """
    
    print("\nSending sample text to LLM parser...\n")
    
    # Call the parser
    result = parse_with_llm(sample_text)
    
    # Print the result
    print("Parser result:")
    print(json.dumps(result, indent=2))
    
    # Check if there was an error
    if "error" in result:
        print(f"\nERROR: {result['error']}")
        sys.exit(1)
    else:
        print("\nTest completed successfully!")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the 'backend' directory.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 