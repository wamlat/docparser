"""
Test script for LLM fallback parser functionality
"""
import os
import json
from app.llm_fallback import parse_with_llm, USE_LLM_PARSER

def test_llm_fallback_parser():
    """
    Test the LLM fallback parser with a sample order text
    """
    # Sample order text
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
    
    # Check if API key is configured
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("WARNING: OpenAI API key not set. Set OPENAI_API_KEY environment variable to run this test.")
        print("Skipping actual API call but continuing with structural test...")
    
    # Try parsing with LLM
    result = parse_with_llm(sample_text)
    
    # Print result with pretty formatting
    print("LLM Fallback Parser Result:")
    print(json.dumps(result, indent=2))
    
    # Check result structure even if API call was not made
    assert "customer" in result, "Missing 'customer' field in result"
    assert "order_id" in result, "Missing 'order_id' field in result"
    assert "shipping_address" in result, "Missing 'shipping_address' field in result"
    assert "line_items" in result, "Missing 'line_items' field in result"
    assert "confidence" in result, "Missing 'confidence' field in result"
    assert "extraction_details" in result, "Missing 'extraction_details' field in result"
    
    # Check if LLM parser is enabled by environment variable
    print(f"USE_LLM_PARSER environment variable is set to: {USE_LLM_PARSER}")
    
    print("LLM fallback parser test completed")

if __name__ == "__main__":
    test_llm_fallback_parser() 