import json
import os
import sys
from app.parser import parse_order_document

def test_parser_fixes():
    """
    Test the parser improvements for the specific issues:
    1. Order ID extraction
    2. Shipping address extraction
    3. SKU extraction
    """
    print("Testing parser improvements...")
    
    # File paths
    test_file = "../test_document.txt"
    
    # Check if the test file exists
    if not os.path.exists(test_file):
        print(f"Error: Test file {test_file} not found")
        return False
    
    # Read the test file
    with open(test_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print("\nDocument text:")
    print("=============")
    print(text)
    print("=============\n")
    
    # Parse the document
    parsed_data = parse_order_document(text)
    
    print("Parsed data:")
    print("===========")
    print(json.dumps(parsed_data, indent=2))
    print("===========\n")
    
    # Check for specific fixes
    fixes_applied = {
        "order_id_fix": False,
        "shipping_address_fix": False,
        "sku_fix": False
    }
    
    # Check order ID fix - should be PO-10023 not "ORDER"
    if parsed_data.get("order_id") == "PO-10023":
        fixes_applied["order_id_fix"] = True
        print("✓ Order ID fix applied successfully")
    else:
        print(f"✗ Order ID fix failed: Got '{parsed_data.get('order_id')}' instead of 'PO-10023'")
    
    # Check shipping address fix - should include "1420" and full address
    expected_address_parts = ["1420", "Edison Lane", "Austin", "TX"]
    if parsed_data.get("shipping_address"):
        address = parsed_data.get("shipping_address")
        if all(part in address for part in expected_address_parts):
            fixes_applied["shipping_address_fix"] = True
            print("✓ Shipping address fix applied successfully")
        else:
            print(f"✗ Shipping address fix failed: Got '{address}', missing some expected parts")
    else:
        print("✗ Shipping address fix failed: No address extracted")
    
    # Check SKU fix - should extract correct SKUs like AXL-9920
    if parsed_data.get("line_items") and len(parsed_data.get("line_items")) > 0:
        skus = [item.get("sku") for item in parsed_data.get("line_items")]
        expected_skus = ["AXL-9920", "MNT-8833"]
        if any(sku in expected_skus for sku in skus):
            fixes_applied["sku_fix"] = True
            print("✓ SKU fix applied successfully")
        else:
            print(f"✗ SKU fix failed: Got {skus}, expected to find one of {expected_skus}")
    else:
        print("✗ SKU fix failed: No line items extracted")
    
    # Overall success
    if all(fixes_applied.values()):
        print("\n🎉 All fixes applied successfully!")
    else:
        failed_fixes = [fix for fix, applied in fixes_applied.items() if not applied]
        print(f"\n⚠️ Some fixes failed: {', '.join(failed_fixes)}")
    
    return all(fixes_applied.values())

if __name__ == "__main__":
    test_parser_fixes() 