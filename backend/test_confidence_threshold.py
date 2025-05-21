"""
Test script for confidence threshold triggering of the LLM fallback parser
"""
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Force module reload to ensure the latest code is used
if 'app.parser_v2' in sys.modules:
    del sys.modules['app.parser_v2']

# Mock the parse_with_llm function before importing parser_v2
sys.modules['app.llm_fallback'] = MagicMock()
from app.llm_fallback import parse_with_llm, USE_LLM_PARSER
parse_with_llm = MagicMock(return_value={"customer": "Test LLM Customer", "source": "llm"})

# Now import the parser
from app.parser_v2 import parse_order_document

def test_confidence_threshold():
    """
    Test that the LLM fallback parser is triggered when confidence is below threshold
    """
    print("\nTesting confidence threshold triggers LLM fallback...")
    
    # Sample order text that would result in low confidence
    # This is intentionally poor quality to trigger low confidence
    sample_text = """
    Some text
    that doesn't look
    like a proper order document
    no clear order id
    no clear customer
    """
    
    # Process with the parser - this should result in low confidence
    result = parse_order_document(sample_text)
    
    # Check if parse_with_llm was called, indicating the threshold triggered
    if parse_with_llm.called:
        print("✅ LLM fallback was triggered due to low confidence")
        print(f"Call count: {parse_with_llm.call_count}")
        print(f"Call arguments: {parse_with_llm.call_args}")
    else:
        print("❌ LLM fallback was NOT triggered")
    
    # Print the result
    print("\nParser Result:")
    print(json.dumps(result, indent=2))
    
    print("\nConfidence threshold test completed")

def test_force_llm_parser():
    """
    Test forcing the LLM parser via environment variable
    """
    print("\nTesting forced LLM parser via USE_LLM_PARSER...")
    
    # Temporarily modify the USE_LLM_PARSER value
    original_value = sys.modules['app.llm_fallback'].USE_LLM_PARSER
    sys.modules['app.llm_fallback'].USE_LLM_PARSER = True
    
    # Reset mock
    parse_with_llm.reset_mock()
    
    # Sample text - this time a higher quality one
    sample_text = """
    ORDER CONFIRMATION
    Order #: PO-12345
    Date: 2023-05-15

    Ship to:
    Acme Corporation
    """
    
    try:
        # Try to process - should immediately use LLM
        parse_order_document(sample_text)
        
        # Check if LLM was called
        if parse_with_llm.called:
            print("✅ LLM parser was forced by USE_LLM_PARSER=True")
            print(f"Call count: {parse_with_llm.call_count}")
        else:
            print("❌ LLM parser was NOT forced despite USE_LLM_PARSER=True")
    finally:
        # Restore original value
        sys.modules['app.llm_fallback'].USE_LLM_PARSER = original_value
    
    print("\nForced LLM parser test completed")

if __name__ == "__main__":
    test_confidence_threshold()
    test_force_llm_parser() 