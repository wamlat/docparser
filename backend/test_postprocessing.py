import json
from app.parser import postprocess_line_items, parse_order_document

def test_line_item_deduplication():
    """Test the deduplication of line items"""
    print("\n===== Testing Line Item Deduplication =====")
    
    # Create test line items with duplicates
    line_items = [
        {
            "sku": {"value": "AXL-9920", "confidence": 0.95, "source": "regex"},
            "quantity": {"value": 25, "confidence": 0.95, "source": "regex"},
            "price": {"value": 12.5, "confidence": 0.95, "source": "regex"}
        },
        {
            "sku": {"value": "AXL-9920", "confidence": 0.9, "source": "regex"},  # Duplicate with lower confidence
            "quantity": {"value": 25, "confidence": 0.9, "source": "regex"},
            "price": {"value": 12.5, "confidence": 0.9, "source": "regex"}
        },
        {
            "sku": {"value": "MNT-8833", "confidence": 0.95, "source": "regex"},
            "quantity": {"value": 10, "confidence": 0.95, "source": "regex"},
            "price": {"value": 44.99, "confidence": 0.95, "source": "regex"}
        }
    ]
    
    print(f"Before: {len(line_items)} line items")
    deduplicated = postprocess_line_items(line_items)
    print(f"After: {len(deduplicated)} line items")
    
    success = len(deduplicated) == 2
    print(f"Test {'PASSED' if success else 'FAILED'}: Line items were {'deduplicated' if success else 'not deduplicated'}")
    return success

def test_sku_validation():
    """Test filtering of invalid SKUs"""
    print("\n===== Testing SKU Validation =====")
    
    # Create test line items with invalid SKUs
    line_items = [
        {
            "sku": {"value": "s", "confidence": 0.95, "source": "regex"},  # Single letter - invalid
            "quantity": {"value": 25, "confidence": 0.95, "source": "regex"},
            "price": {"value": 12.5, "confidence": 0.95, "source": "regex"}
        },
        {
            "sku": {"value": "AXL-9920", "confidence": 0.95, "source": "regex"},  # Valid SKU
            "quantity": {"value": 25, "confidence": 0.95, "source": "regex"},
            "price": {"value": 12.5, "confidence": 0.95, "source": "regex"}
        },
        {
            "sku": {"value": "12", "confidence": 0.95, "source": "regex"},  # Just numbers - invalid
            "quantity": {"value": 10, "confidence": 0.95, "source": "regex"},
            "price": {"value": 44.99, "confidence": 0.95, "source": "regex"}
        },
        {
            "sku": {"value": "IMG-001", "confidence": 0.95, "source": "regex"},  # Exception format - should be kept
            "quantity": {"value": 5, "confidence": 0.95, "source": "regex"},
            "price": {"value": 19.99, "confidence": 0.95, "source": "regex"}
        }
    ]
    
    print(f"Before: {len(line_items)} line items with SKUs: {[item['sku']['value'] for item in line_items]}")
    filtered = postprocess_line_items(line_items)
    print(f"After: {len(filtered)} line items with SKUs: {[item['sku']['value'] for item in filtered]}")
    
    # Check if invalid SKUs were removed and valid ones kept
    invalid_removed = not any(item["sku"]["value"] in ["s", "12"] for item in filtered)
    valid_kept = any(item["sku"]["value"] == "AXL-9920" for item in filtered)
    exception_kept = any(item["sku"]["value"] == "IMG-001" for item in filtered)
    
    success = invalid_removed and valid_kept and exception_kept
    print(f"Test {'PASSED' if success else 'FAILED'}: Invalid SKUs were "
          f"{'properly filtered' if success else 'not properly filtered'}")
    return success

def test_shipping_address_trimming():
    """Test trimming of shipping address to exclude line items"""
    print("\n===== Testing Shipping Address Trimming =====")
    
    # Test text with shipping address that includes line items
    test_text = """PURCHASE ORDER
Order ID: PO-10023
Customer: NovaTech Industries
Ship To:
NovaTech Industries
1420 Edison Lane
Austin, TX 73301
Line Items:
1. Part #AXL-9920 | Qty: 25 | Unit Price: $12.50
2. Part #MNT-8833 | Qty: 10 | Unit Price: $44.99"""
    
    # Parse the document
    parsed_data = parse_order_document(test_text)
    
    # Check if shipping address includes line item text
    address = parsed_data["shipping_address"]
    print(f"Extracted address: '{address}'")
    
    success = "Line Items" not in address and "Part #" not in address
    print(f"Test {'PASSED' if success else 'FAILED'}: Line items were "
          f"{'properly excluded from address' if success else 'not excluded from address'}")
    return success

def test_order_id_correction():
    """Test correction of order ID from 'ORDER' to actual ID"""
    print("\n===== Testing Order ID Correction =====")
    
    # Test text with ORDER ID that would be extracted as ORDER without fix
    test_text = """PURCHASE ORDER
Order ID: PO-10023
Customer: NovaTech Industries"""
    
    # Create a modified version that would normally extract ORDER
    test_text_modified = test_text.replace("Order ID: PO-10023", "order PO-10023")
    
    # Parse both documents
    parsed_data = parse_order_document(test_text)
    parsed_data_modified = parse_order_document(test_text_modified)
    
    print(f"Original extraction: '{parsed_data['order_id']}'")
    print(f"Modified extraction: '{parsed_data_modified['order_id']}'")
    
    success = parsed_data["order_id"] == "PO-10023"
    success_modified = not parsed_data_modified["order_id"] == "ORDER"
    
    print(f"Test {'PASSED' if success else 'FAILED'}: Original order ID was "
          f"{'correctly extracted' if success else 'not correctly extracted'}")
    print(f"Test {'PASSED' if success_modified else 'FAILED'}: Modified order ID was "
          f"{'correctly handled' if success_modified else 'not correctly handled'}")
    return success and success_modified

def test_whitespace_normalization():
    """Test normalization of whitespace in text fields"""
    print("\n===== Testing Whitespace Normalization =====")
    
    # Test text with excessive whitespace
    test_text = """PURCHASE ORDER
Order  ID:    PO-10023
Customer:   NovaTech    Industries
Ship   To:
NovaTech   Industries
1420   Edison   Lane,   
Austin,   TX   73301,  """
    
    # Parse the document
    parsed_data = parse_order_document(test_text)
    
    # Check normalized fields
    customer = parsed_data["customer"]
    address = parsed_data["shipping_address"]
    
    print(f"Normalized customer: '{customer}'")
    print(f"Normalized address: '{address}'")
    
    success_customer = "  " not in customer  # No double spaces
    success_address = "  " not in address and not address.endswith(",")  # No double spaces or trailing commas
    
    success = success_customer and success_address
    print(f"Test {'PASSED' if success else 'FAILED'}: Whitespace was "
          f"{'properly normalized' if success else 'not properly normalized'}")
    return success

def run_all_tests():
    """Run all postprocessing tests"""
    print("===== Running All Postprocessing Tests =====")
    
    test_results = [
        test_line_item_deduplication(),
        test_sku_validation(),
        test_shipping_address_trimming(),
        test_order_id_correction(),
        test_whitespace_normalization()
    ]
    
    # Print summary
    print("\n===== Test Summary =====")
    print(f"Total tests: {len(test_results)}")
    print(f"Passed: {sum(test_results)}")
    print(f"Failed: {len(test_results) - sum(test_results)}")
    
    if all(test_results):
        print("\n🎉 All postprocessing tests passed!")
    else:
        print("\n⚠️ Some tests failed. Please check the logs above.")
    
    return all(test_results)

if __name__ == "__main__":
    run_all_tests() 