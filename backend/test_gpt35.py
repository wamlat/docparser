#!/usr/bin/env python3
"""
Test script to verify GPT-3.5 Turbo integration with the document parser.
This script directly tests the LLM fallback module with a sample order document.
"""

import os
import sys
import json
from dotenv import load_dotenv
from app.llm_fallback import parse_with_llm, USE_LLM_PARSER, LLM_MODEL

# Set up environment
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

def test_gpt35_turbo():
    """Test the GPT-3.5 Turbo parser with a sample document."""
    
    # Check if OpenAI API key is set
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        print("ERROR: OpenAI API key not set. Please set it in your .env file.")
        return False
    
    # Sample order document text for testing
    sample_text = """
    ORDER #PO-10023
    Date: 2023-04-15
    
    Customer: NovaTech Industries
    Ship to:
    1420 Edison Lane
    Austin, TX 73301
    
    Line Items:
    1. Part #AXL-9920 | Qty: 25 | Unit Price: $12.50
    2. Part #MNT-8833 | Qty: 10 | Unit Price: $44.99
    
    Total: $824.90
    """
    
    print("\n====== GPT-3.5 Turbo Parser Test ======")
    print(f"USE_LLM_PARSER: {USE_LLM_PARSER}")
    print(f"LLM_MODEL: {LLM_MODEL}")
    print("\nSample Document:")
    print("----------------")
    print(sample_text)
    print("----------------")
    
    # Call the LLM parser
    print("\nSending to LLM parser...")
    try:
        result = parse_with_llm(sample_text)
        
        print("\nParsing Result:")
        print(json.dumps(result, indent=2))
        
        # Verify the result contains expected fields
        required_fields = ["customer", "order_id", "shipping_address", "line_items"]
        if all(field in result for field in required_fields):
            print("\n✅ Test PASSED: All required fields found in result")
            
            # Check number of line items
            if len(result["line_items"]) == 2:
                print("✅ Line items count correct")
            else:
                print(f"❌ Line items count incorrect: Expected 2, got {len(result['line_items'])}")
                
            # Check order_id
            if result["order_id"] == "PO-10023":
                print("✅ Order ID correctly extracted")
            else:
                print(f"❌ Order ID incorrect: Expected 'PO-10023', got '{result['order_id']}'")
                
            return True
        else:
            missing = [f for f in required_fields if f not in result]
            print(f"\n❌ Test FAILED: Missing fields: {missing}")
            return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Make sure we can import from the app package
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Run the test
    success = test_gpt35_turbo()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 