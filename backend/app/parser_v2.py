import re
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
import numpy as np
from app.ner_model import predict_entities, group_entities
import os
from app.parser_stats import increment_llm_forced_counter, increment_ner_counter, increment_llm_fallback_counter

# Constants
CONFIDENCE_THRESHOLD = 0.7  # Confidence threshold for warnings

# Load NER model and tokenizer
print("Loading NER model and tokenizer for parser_v2...")
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
print("NER model and tokenizer loaded successfully")

def postprocess_line_items(items):
    """
    Postprocess line items to deduplicate and filter invalid entries.
    
    Args:
        items (list): List of line item dictionaries
        
    Returns:
        list: Cleaned list of line items
    """
    print("\n===== CRITICAL DEBUG: Starting postprocess_line_items =====")
    print(f"Input items count: {len(items)}")
    for i, item in enumerate(items):
        sku = item.get("sku", {}).get("value", "NONE")
        print(f"Item {i}: SKU={sku}, Confidence={item.get('sku', {}).get('confidence', 'NONE')}")
    
    # Dictionary to track unique items
    unique_items = {}
    valid_items = []
    
    # Define more flexible SKU patterns to match real-world variations
    # Primary pattern: 2+ letters followed by hyphen and 2+ digits (e.g., AXL-9920)
    primary_pattern = re.compile(r'^[A-Za-z]{2,}-\d{2,}$')
    
    # Secondary patterns for exceptions
    alpha_num_pattern = re.compile(r'^[A-Za-z]{2,}\d{2,}$')  # e.g., AXL9920
    triple_alpha_pattern = re.compile(r'^[A-Za-z]{3,}-[A-Za-z0-9]{3,}$')  # e.g., ABC-X10
    
    # Invalid patterns - single characters
    invalid_pattern = re.compile(r'^[a-zA-Z]{1}$|^\d{1,2}$')  # Single letters or 1-2 digits
    
    # Explicitly banned SKUs (direct matches)
    banned_skus = ['s', 'S', 'x', 'X', '1', '2', '12', '123']
    
    # Store all valid items before processing
    all_valid_items = []
    
    for item in items:
        # Skip items with invalid SKUs
        sku = item.get("sku", {}).get("value", "")
        
        # Direct check for explicitly banned SKUs (highest priority check)
        if sku in banned_skus:
            print(f"CRITICAL DEBUG: Skipping explicitly banned SKU: '{sku}'")
            continue
        
        # Skip empty or very short SKUs
        if not sku or len(sku) < 3:
            print(f"DEBUG: Skipping item with invalid SKU: '{sku}' (too short)")
            continue
        
        # Skip single letter or digit SKUs which are likely extraction errors
        if invalid_pattern.match(sku):
            print(f"DEBUG: Skipping definitely invalid SKU: '{sku}' (single letter/digit)")
            continue
            
        # Check if SKU matches any of our accepted patterns
        is_valid = False
        
        if primary_pattern.match(sku):
            print(f"DEBUG: Valid primary format SKU: '{sku}'")
            is_valid = True
        elif alpha_num_pattern.match(sku):
            print(f"DEBUG: Valid alphanumeric SKU: '{sku}'")
            is_valid = True
        elif triple_alpha_pattern.match(sku):
            print(f"DEBUG: Valid triple alpha format SKU: '{sku}'")
            is_valid = True
        elif len(sku) >= 4 and sku[0].isalpha():
            # More lenient check for longer SKUs that start with a letter
            print(f"DEBUG: Allowing non-standard but acceptable SKU format: '{sku}'")
            is_valid = True
        else:
            print(f"DEBUG: Skipping invalid SKU: '{sku}' (format doesn't match any patterns)")
            continue
        
        # Add to valid items list if it passed all checks
        all_valid_items.append(item)
    
    # Print all valid items after filtering
    print(f"Valid items after pattern filtering: {len(all_valid_items)}")
    for i, item in enumerate(all_valid_items):
        print(f"Valid Item {i}: SKU={item.get('sku', {}).get('value', 'NONE')}")
    
    # Process valid items for deduplication
    for item in all_valid_items:
        sku = item.get("sku", {}).get("value", "")
        
        # Create a unique key for this item
        key = (sku, item.get("quantity", {}).get("value", 0), item.get("price", {}).get("value", 0))
        
        # If this is a new unique item, or it has higher confidence than a previous one
        if key not in unique_items or item.get("sku", {}).get("confidence", 0) > unique_items[key].get("sku", {}).get("confidence", 0):
            unique_items[key] = item
            print(f"DEBUG: Added/updated unique item: '{sku}'")
        else:
            print(f"DEBUG: Skipped duplicate item with lower confidence: '{sku}'")
    
    # Convert back to list
    valid_items = list(unique_items.values())
    
    print(f"Final output items count: {len(valid_items)}")
    print("Final SKUs in output:")
    for i, item in enumerate(valid_items):
        sku = item.get("sku", {}).get("value", "NONE")
        print(f"Result Item {i}: SKU='{sku}'")
    print("===== CRITICAL DEBUG: Finished postprocess_line_items =====\n")
    
    return valid_items

def compute_token_confidence(logits):
    """
    Compute confidence scores for each token using softmax.
    
    Args:
        logits (torch.Tensor): Raw logits from the model
        
    Returns:
        list: Confidence scores for each token
    """
    # Apply softmax to compute probability distributions
    probs = torch.nn.functional.softmax(logits, dim=2)
    
    # Get the maximum probability for each token
    max_probs, _ = torch.max(probs, dim=2)
    
    return max_probs.tolist()

def extract_ner(text):
    """
    Extract named entities from text using the BERT NER model.
    
    Args:
        text (str): Text to process
        
    Returns:
        list: List of tuples (entity, entity_type, confidence)
    """
    # Tokenize the text
    inputs = tokenizer(text, truncation=True, return_tensors="pt", return_offsets_mapping=True, padding=True)
    tokens = inputs.tokens()
    offset_mapping = inputs["offset_mapping"][0].tolist()
    
    # Perform NER
    with torch.no_grad():
        outputs = model(**{k: v for k, v in inputs.items() if k != "offset_mapping"})
    
    # Get the predictions and confidence scores
    predictions = torch.argmax(outputs.logits, dim=2)[0].tolist()
    confidences = compute_token_confidence(outputs.logits)[0]
    
    # Map predictions to named entities
    idx2tag = {i: tag for i, tag in enumerate(model.config.id2label.values())}
    
    entities = []
    current_entity = None
    current_entity_type = None
    current_confidences = []
    
    for i, (pred, token, offset, conf) in enumerate(zip(predictions, tokens, offset_mapping, confidences)):
        # Skip special tokens like [CLS], [SEP]
        if offset[0] == offset[1]:  # Special token
            continue
        
        tag = idx2tag[pred]
        
        # Handle B- (beginning of entity) tags
        if tag.startswith("B-"):
            # If we were building an entity, add it to the list
            if current_entity is not None:
                avg_confidence = sum(current_confidences) / len(current_confidences)
                entities.append((current_entity, current_entity_type, avg_confidence))
            
            # Start a new entity
            current_entity = token.replace("##", "")
            current_entity_type = tag[2:]
            current_confidences = [conf]
        
        # Handle I- (inside entity) tags
        elif tag.startswith("I-") and current_entity is not None and current_entity_type == tag[2:]:
            # Continue building the entity
            current_entity += token.replace("##", "")
            current_confidences.append(conf)
        
        # Handle O (outside) tags
        else:
            # If we were building an entity, add it to the list
            if current_entity is not None:
                avg_confidence = sum(current_confidences) / len(current_confidences)
                entities.append((current_entity, current_entity_type, avg_confidence))
                current_entity = None
                current_entity_type = None
                current_confidences = []
    
    # Add the last entity if we were building one
    if current_entity is not None:
        avg_confidence = sum(current_confidences) / len(current_confidences)
        entities.append((current_entity, current_entity_type, avg_confidence))
    
    # Post-process entities
    processed_entities = []
    for entity, entity_type, confidence in entities:
        # Clean the entity text
        entity = entity.replace("##", "")
        # Skip entities with very low confidence
        if confidence > 0.3:
            processed_entities.append((entity, entity_type, confidence))
    
    return processed_entities

def extract_entities(text):
    """
    Extract structured entities from raw text using NER and regex.
    
    Args:
        text (str): Raw text to process
        
    Returns:
        dict: Dictionary with structured order information
    """
    # Initialize structured data with confidence
    structured_data = {
        "customer": {"value": "", "confidence": 0.0, "source": ""},
        "order_id": {"value": "", "confidence": 0.0, "source": ""},
        "line_items": [],
        "shipping_address": {"value": "", "confidence": 0.0, "source": ""}
    }
    
    # CRITICAL FIX: First pass to check for PO-XXXXX format order ID
    po_id_match = re.search(r'order\s*(?:id|number|#|)?\s*[\:\#\s]\s*(PO-\d+)', text, re.IGNORECASE)
    if po_id_match:
        structured_data["order_id"]["value"] = po_id_match.group(1).strip().upper()
        structured_data["order_id"]["confidence"] = 0.99  # Highest confidence for direct PO match
        structured_data["order_id"]["source"] = "regex-po-direct"
        print(f"Direct PO match found: {structured_data['order_id']['value']}")
    
    # If no direct PO match, try other order ID patterns
    if not structured_data["order_id"]["value"]:
        # Extract Order ID - General pattern
        order_id_match = re.search(r'order\s*(?:id|number|#)?\s*[\:\#]?\s*([a-zA-Z0-9\-\_]+)', text, re.IGNORECASE)
        if order_id_match:
            structured_data["order_id"]["value"] = order_id_match.group(1).strip().upper()
            structured_data["order_id"]["confidence"] = 0.95
            structured_data["order_id"]["source"] = "regex"
        
        # Additional pattern for PO or similar prefixed order IDs
        alt_po_match = re.search(r'(?:PO|order)[\s\-]*(?:id|number|#)?[\s\:\#]*([a-zA-Z0-9\-\_]+)', text, re.IGNORECASE)
        if alt_po_match and (not structured_data["order_id"]["value"] or len(alt_po_match.group(1)) > len(structured_data["order_id"]["value"])):
            structured_data["order_id"]["value"] = alt_po_match.group(1).strip().upper()
            structured_data["order_id"]["confidence"] = 0.98
            structured_data["order_id"]["source"] = "regex-po"
    
    # Extract Customer
    customer_match = re.search(r'customer\s*[\:\#]?\s*([a-zA-Z0-9\s]+(?:$|\n))', text, re.IGNORECASE)
    if customer_match:
        structured_data["customer"]["value"] = customer_match.group(1).strip()
        structured_data["customer"]["confidence"] = 0.95
        structured_data["customer"]["source"] = "regex"
    
    # Enhanced Shipping Address extraction with multi-line support
    # First try to find a shipping address section
    ship_to_section = re.search(r'ship\s*to\s*:?\s*([\s\S]+?)(?=\n\s*\n|\n[A-Za-z]+\s*:|\Z)', text, re.IGNORECASE)
    if ship_to_section:
        # Get all lines from the Ship To section
        address_lines = ship_to_section.group(1).strip().split('\n')
        
        # Skip the first line if it's just a company name (already captured in customer)
        if len(address_lines) > 1 and structured_data["customer"]["value"] and address_lines[0].strip() == structured_data["customer"]["value"]:
            address_lines = address_lines[1:]
        
        # Filter lines to only include those starting with capital letters or numbers (proper address format)
        filtered_address_lines = []
        for line in address_lines:
            line_strip = line.strip()
            # Only include lines that start with capital letters or numbers
            if line_strip and re.match(r"^[A-Z0-9]", line_strip):
                filtered_address_lines.append(line_strip)
            # Stop at indicators like "Ref #:" or "Thanks"
            elif line_strip.startswith(("Ref #:", "Thanks")):
                break
        
        # Join the filtered lines
        full_address = ', '.join(filtered_address_lines)
        structured_data["shipping_address"]["value"] = full_address
        structured_data["shipping_address"]["confidence"] = 0.92
        structured_data["shipping_address"]["source"] = "regex-multi"
    else:
        # Fallback to basic address pattern if no section found
        address_match = re.search(r'(?:shipping|delivery)?\s*address\s*[\:\#]?\s*([a-zA-Z0-9\s\,\-\.]+(?:$|\n))', text, re.IGNORECASE)
        if address_match:
            # Extract the address and filter it
            address_text = address_match.group(1).strip()
            address_lines = address_text.split('\n')
            
            # Filter to only include lines starting with capital letters or numbers
            filtered_address_lines = []
            for line in address_lines:
                line_strip = line.strip()
                if line_strip and re.match(r"^[A-Z0-9]", line_strip):
                    filtered_address_lines.append(line_strip)
                elif line_strip.startswith(("Ref #:", "Thanks")):
                    break
                
            structured_data["shipping_address"]["value"] = ', '.join(filtered_address_lines)
            structured_data["shipping_address"]["confidence"] = 0.85
            structured_data["shipping_address"]["source"] = "regex"
    
    # Enhanced SKU extraction
    # Extract line items using regex patterns
    # Look for Part #XXX-XXXX pattern
    part_matches = re.finditer(r'(?:part|item)\s*\#([a-zA-Z0-9\-]+)\s*\|\s*(?:qty|quantity)\s*:\s*(\d+)\s*\|\s*(?:(?:unit\s*)?price)\s*:\s*\$?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    
    for match in part_matches:
        sku = match.group(1).strip()
        quantity = int(match.group(2))
        price = float(match.group(3))
        
        line_item = {
            "sku": {"value": sku, "confidence": 0.95, "source": "regex-part"},
            "quantity": {"value": quantity, "confidence": 0.95, "source": "regex"},
            "price": {"value": price, "confidence": 0.95, "source": "regex"}
        }
        
        structured_data["line_items"].append(line_item)
    
    # If we didn't find line items with the enhanced pattern, try the original pattern
    if not structured_data["line_items"]:
        sku_matches = re.finditer(r'(?:sku|item|product)\s*:?\s*([a-zA-Z0-9\-]+).*?(?:qty|quantity)\s*:?\s*(\d+).*?(?:price)\s*:?\s*\$?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        
        for match in sku_matches:
            sku = match.group(1).strip()
            quantity = int(match.group(2))
            price = float(match.group(3))
            
            line_item = {
                "sku": {"value": sku, "confidence": 0.9, "source": "regex"},
                "quantity": {"value": quantity, "confidence": 0.9, "source": "regex"},
                "price": {"value": price, "confidence": 0.9, "source": "regex"}
            }
            
            structured_data["line_items"].append(line_item)
    
    # Process the text line by line to extract structured line items
    current_line_item = None
    
    for line in text.splitlines():
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if the line could be part of a line item
        sku_match = re.search(r'(?:sku|part|item)\s*(?:\#|number)?[:\s]*\s*([a-zA-Z0-9\-]+)', line, re.IGNORECASE)
        qty_match = re.search(r'(?:qty|quantity)[:\s]*\s*(\d+)', line, re.IGNORECASE)
        price_match = re.search(r'(?:price|cost)[:\s]*\s*\$?(\d+(?:\.\d+)?)', line, re.IGNORECASE)
        
        # Additional regex pattern for line items with Part #XXX-XXXX format
        part_match = re.search(r'(?:part|item)\s*\#([a-zA-Z0-9\-]+)', line, re.IGNORECASE)
        
        # If we found either a sku, qty, or price, we might be in a line item
        if sku_match or qty_match or price_match or part_match:
            # If we're not already building a line item, start a new one
            if not current_line_item:
                current_line_item = {}
            
            # Update the line item with any new information
            if sku_match and "sku" not in current_line_item:
                current_line_item["sku"] = {
                    "value": sku_match.group(1),
                    "confidence": 0.8,
                    "source": "regex-line"
                }
            elif part_match and "sku" not in current_line_item:
                current_line_item["sku"] = {
                    "value": part_match.group(1),
                    "confidence": 0.9,
                    "source": "regex-part"
                }
            
            if qty_match and "quantity" not in current_line_item:
                current_line_item["quantity"] = {
                    "value": int(qty_match.group(1)),
                    "confidence": 0.8,
                    "source": "regex-line"
                }
            
            if price_match and "price" not in current_line_item:
                current_line_item["price"] = {
                    "value": float(price_match.group(1)),
                    "confidence": 0.8,
                    "source": "regex-line"
                }
            
            # If we have a complete line item, add it to our results and start a new one
            if "sku" in current_line_item and "quantity" in current_line_item and "price" in current_line_item:
                structured_data["line_items"].append(current_line_item)
                current_line_item = None
        else:
            # This line doesn't contain recognizable line item data
            # If we were building a line item, finish it up
            if current_line_item and "sku" in current_line_item:
                # Add defaults for missing fields
                if "quantity" not in current_line_item:
                    current_line_item["quantity"] = {
                        "value": 1,
                        "confidence": 0.5,
                        "source": "default",
                        "warning": True
                    }
                if "price" not in current_line_item:
                    current_line_item["price"] = {
                        "value": 0.0,
                        "confidence": 0.5,
                        "source": "default",
                        "warning": True
                    }
                structured_data["line_items"].append(current_line_item)
                current_line_item = None
    
    # Add the last line item if it's not empty and has at least a SKU
    if current_line_item and "sku" in current_line_item:
        if "quantity" not in current_line_item:
            current_line_item["quantity"] = {
                "value": 1,
                "confidence": 0.5,
                "source": "default",
                "warning": True
            }
        if "price" not in current_line_item:
            current_line_item["price"] = {
                "value": 0.0,
                "confidence": 0.5,
                "source": "default",
                "warning": True
            }
        if current_line_item not in structured_data["line_items"]:
            structured_data["line_items"].append(current_line_item)
    
    # Override "ORDER" with regex extraction if needed
    if structured_data["order_id"]["value"] == "ORDER" or structured_data["order_id"]["value"] == "":
        print("Attempting to extract order ID with additional fallback patterns...")
        
        # Try different patterns to extract PO numbers
        po_patterns = [
            r'Order\s*ID[:\s]*([A-Z0-9\-]+)',  # Order ID: ABC-1234
            r'PO\s*(?:ID|Number|#)?[:\s]*([A-Z0-9\-]+)',  # PO Number: ABC-1234
            r'(?:Order|Purchase)\s*(?:Number|#)[:\s]*([A-Z0-9\-]+)',  # Order Number: ABC-1234
            r'(?:Order|PO)[:\s]*([A-Z0-9\-]+)',  # Order: ABC-1234
            r'(?:Order|PO)[:\s\#]*([A-Z0-9\-]+)',  # PO# ABC-1234
            r'(?<![a-zA-Z])(?:PO|ORDER)[:\s\-]*([A-Z0-9\-]+)',  # ORDER-ABC-1234
            r'(?:^|\n)(?:PO|Order)[\:\s\-\#]*([A-Za-z0-9\-]+)',  # Beginning of line: Order ABC-1234
            r'Ref\s*#[:\s]*([A-Z0-9\-]+)'  # Ref #: ABC-1234
        ]
        
        for pattern in po_patterns:
            order_id_match = re.search(pattern, text, re.IGNORECASE)
            if order_id_match:
                new_order_id = order_id_match.group(1).strip()
                print(f"Found order ID: '{new_order_id}' using pattern: {pattern}")
                structured_data["order_id"]["value"] = new_order_id
                structured_data["order_id"]["source"] = "regex-fallback"
                structured_data["order_id"]["confidence"] = 0.9
                break
    
    # Add informal line item regex pattern
    # Example: "12x of HTR-1204 @ $32.00"
    informal_items = re.findall(r"(\d+)[xX]\s+of\s+([A-Z0-9\-]+)\s+@\s+\$?(\d+\.?\d*)", text, re.IGNORECASE)
    for qty, sku, price in informal_items:
        # Create line item from informal pattern
        line_item = {
            "sku": {"value": sku.strip(), "confidence": 0.85, "source": "regex-informal"},
            "quantity": {"value": int(qty), "confidence": 0.85, "source": "regex-informal"},
            "price": {"value": float(price), "confidence": 0.85, "source": "regex-informal"}
        }
        structured_data["line_items"].append(line_item)
        print(f"Found informal line item: {qty}x of {sku} @ ${price}")
    
    return structured_data

def parse_order_document(text):
    """
    Main function to parse an order document text.
    
    Args:
        text (str): Raw text from a document
        
    Returns:
        dict: Structured order data
    """
    print("\n===== DEBUG: Starting parse_order_document (PARSER_V2) =====")
    
    # Check if we should use LLM parser directly
    try:
        from app.llm_fallback import USE_LLM_PARSER, parse_with_llm
        
        # Get confidence threshold from environment (default 0.6)
        CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.6"))
        
        if USE_LLM_PARSER:
            print("USE_LLM_PARSER flag is enabled, using LLM parser directly")
            increment_llm_forced_counter()  # Track forced LLM usage
            return parse_with_llm(text)
    except ImportError:
        print("LLM fallback module not available, continuing with standard parsing")
        CONFIDENCE_THRESHOLD = 0.6  # Default if module not available
    except ValueError:
        print("Invalid CONFIDENCE_THRESHOLD value in environment, using default 0.6")
        CONFIDENCE_THRESHOLD = 0.6  # Default if value is invalid
    
    # Extract structured data from text
    structured_data = extract_entities(text)
    
    print(f"Before postprocessing: {len(structured_data['line_items'])} line items")
    print("Calling postprocess_line_items...")
    
    # Deduplicate and filter line items
    structured_data["line_items"] = postprocess_line_items(structured_data["line_items"])
    
    print(f"After postprocessing: {len(structured_data['line_items'])} line items")
    
    # Normalize whitespace in text fields
    for field in ["customer", "order_id", "shipping_address"]:
        if structured_data[field]["value"]:
            # Normalize whitespace: replace multiple spaces with single space
            value = re.sub(r'\s+', ' ', structured_data[field]["value"])
            # Remove trailing commas and whitespace
            value = re.sub(r'[,\s]+$', '', value)
            structured_data[field]["value"] = value
    
    # Flag and exclude fields with very low confidence
    for field in ["customer", "order_id", "shipping_address"]:
        if structured_data[field]["confidence"] < 0.5 and structured_data[field]["source"] != "regex-fallback":
            structured_data[field]["warning"] = True
            
    # Extract shipping address up to Line Items section
    if structured_data["shipping_address"]["value"]:
        address = structured_data["shipping_address"]["value"]
        print(f"Original shipping address: '{address}'")
        
        # Define patterns that indicate the beginning of line items
        line_item_indicators = [
            "Line Items:", 
            "Items:", 
            "Products:", 
            "Order Details:", 
            "Part #", 
            "SKU", 
            "Quantity",
            "Item #",
            "Ref #:",  # Added indicator for "Ref #"
            "Thanks"   # Added indicator for "Thanks"
        ]
        
        # Find where any line item indicator starts
        cutoff_idx = len(address)
        for indicator in line_item_indicators:
            idx = address.find(indicator)
            if idx > 0 and idx < cutoff_idx:
                cutoff_idx = idx
                print(f"Found line item indicator '{indicator}' at position {idx}")
        
        # Also check for numbered items that might indicate line items
        numbered_item_idx = re.search(r',\s*\d+\.', address)
        if numbered_item_idx and numbered_item_idx.start() < cutoff_idx:
            cutoff_idx = numbered_item_idx.start()
            print(f"Found numbered item indicator at position {cutoff_idx}")
            
        # Trim address if line items were found
        if cutoff_idx < len(address):
            address = address[:cutoff_idx].strip()
            print(f"Trimmed address at index {cutoff_idx}")
        
        # Additional filtering for properly formatted address lines
        address_parts = [part.strip() for part in address.split(',')]
        filtered_parts = []
        
        for part in address_parts:
            # Only keep parts that start with capital letters or numbers (proper address format)
            if part and re.match(r"^[A-Z0-9]", part):
                filtered_parts.append(part)
            # Stop at blank lines or informal phrases
            elif part.lower().startswith(("our warehouse", "your warehouse", "ref #", "thanks", "reference")):
                print(f"Stopping at informal phrase: '{part}'")
                break
        
        # Cleanup: remove trailing commas and normalize whitespace
        address = ', '.join(filtered_parts)
        address = re.sub(r',\s*$', '', address)
        address = re.sub(r'\s+', ' ', address).strip()
        print(f"Cleaned shipping address: '{address}'")
        
        structured_data["shipping_address"]["value"] = address
    
    # Add fallback for customer name based on "Ship to" or "warehouse:"
    if not structured_data["customer"]["value"] or structured_data["customer"]["confidence"] < 0.7:
        # Look for informal customer references like "Ship to" or "warehouse:"
        ship_to_match = re.search(r'ship\s+to\s*[:\s]*([A-Za-z0-9\s\,]+?)(?=\n|\r|$)', text, re.IGNORECASE)
        warehouse_match = re.search(r'(?:our|your)\s+warehouse[:\s]*([A-Za-z0-9\s\,]+?)(?=\n|\r|$)', text, re.IGNORECASE)
        
        if ship_to_match:
            structured_data["customer"]["value"] = ship_to_match.group(1).strip()
            structured_data["customer"]["confidence"] = 0.8
            structured_data["customer"]["source"] = "regex-ship-to"
            print(f"Found customer name from 'Ship to': {structured_data['customer']['value']}")
        elif warehouse_match:
            structured_data["customer"]["value"] = warehouse_match.group(1).strip()
            structured_data["customer"]["confidence"] = 0.75
            structured_data["customer"]["source"] = "regex-warehouse"
            print(f"Found customer name from warehouse reference: {structured_data['customer']['value']}")
    
    # Flatten the output for backward compatibility
    flat_output = {
        "customer": structured_data["customer"]["value"],
        "order_id": structured_data["order_id"]["value"],
        "shipping_address": structured_data["shipping_address"]["value"],
        "line_items": []
    }
    
    # FINAL SAFETY CHECK: Define banned SKUs
    banned_skus = ['s', 'S', 'x', 'X', '1', '2', '12', '123', '0']
    
    # Flatten line items with a final safety check
    for item in structured_data["line_items"]:
        sku = item["sku"]["value"]
        
        # Skip banned SKUs in final flattening step
        if sku in banned_skus:
            print(f"FINAL SAFETY: Blocked banned SKU: '{sku}' from output")
            continue
            
        # Skip single character SKUs 
        if len(sku) <= 1:
            print(f"FINAL SAFETY: Blocked single character SKU: '{sku}' from output")
            continue
            
        flat_item = {
            "sku": sku,
            "quantity": item["quantity"]["value"],
            "price": item["price"]["value"]
        }
        flat_output["line_items"].append(flat_item)
    
    print(f"Final line items count after safety check: {len(flat_output['line_items'])}")
    print("Final output SKUs:")
    for i, item in enumerate(flat_output["line_items"]):
        print(f"Final Item {i}: SKU='{item['sku']}'")
    
    # Calculate confidence scores
    confidence = {
        "customer": structured_data["customer"]["confidence"],
        "order_id": structured_data["order_id"]["confidence"],
        "shipping_address": structured_data["shipping_address"]["confidence"],
        "line_items": sum(item["sku"]["confidence"] for item in structured_data["line_items"]) / max(1, len(structured_data["line_items"]))
    }
    
    # Add overall confidence
    confidence["overall"] = sum(confidence.values()) / len(confidence)
    
    # Add confidence scores to the output
    flat_output["confidence"] = confidence
    
    # Add detailed extraction data
    flat_output["extraction_details"] = {
        "customer": structured_data["customer"],
        "order_id": structured_data["order_id"],
        "shipping_address": structured_data["shipping_address"],
        "line_items": structured_data["line_items"]
    }
    
    print("===== DEBUG: Finished parse_order_document (PARSER_V2) =====\n")
    
    # Check if we should use LLM fallback based on confidence threshold
    try:
        # Only use LLM fallback if confidence is below threshold
        from app.llm_fallback import parse_with_llm
        from app.parser_stats import increment_llm_fallback_counter
        
        if confidence["overall"] < CONFIDENCE_THRESHOLD:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"LLM fallback parser used due to low confidence: {confidence['overall']:.2f} (threshold: {CONFIDENCE_THRESHOLD})")
            
            # Call LLM parser
            llm_result = parse_with_llm(text)
            
            # Use LLM result if it was successful (no error in result)
            if llm_result and "error" not in llm_result:
                print(f"Using LLM fallback parser result due to low confidence ({confidence['overall']:.2f} < {CONFIDENCE_THRESHOLD})")
                increment_llm_fallback_counter()  # Track LLM fallback usage
                return llm_result
            else:
                # Log the error but use original result
                print(f"LLM fallback parser failed. Using original result despite low confidence.")
                if llm_result and "error" in llm_result:
                    error_msg = llm_result["error"]
                    if "rate limit" in error_msg.lower() or "429" in error_msg:
                        logger.warning(f"OpenAI API rate limit error: {error_msg}. Continuing with standard parser results.")
                    else:
                        logger.error(f"LLM fallback error: {error_msg}")
    except ImportError:
        print("LLM fallback module not available for confidence check")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error using LLM fallback parser: {str(e)}")
    
    # If we reach here, we're using NER/regex parser results
    increment_ner_counter()  # Track NER usage
    return flat_output 