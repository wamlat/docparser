import re
from app.ner_model import predict_entities, group_entities

# Constants
CONFIDENCE_THRESHOLD = 0.6  # Threshold for low confidence warning

def clean_text(text):
    """
    Clean and normalize text before processing.
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    return text

# Regex fallback functions
def extract_sku_regex(text, context=None):
    """Extract SKU using regex patterns"""
    context = context or text
    # Try different patterns for SKUs
    patterns = [
        r'(?:sku|item|product)\s*[\:\#]?\s*([a-zA-Z0-9\-\_]+)',  # SKU: X123
        r'\b([A-Z][A-Z0-9\-\_]{2,})\b'  # Standalone SKU like ABC123
    ]
    
    for pattern in patterns:
        if context:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1), "regex"
    
    return None, None

def extract_quantity_regex(text, context=None):
    """Extract quantity using regex patterns"""
    context = context or text
    patterns = [
        r'(?:qty|quantity)\s*[\:\#]?\s*(\d+)',  # Quantity: 10
        r'(\d+)\s*(?:units?|pcs|pieces)'  # 10 units, 10 pcs
    ]
    
    for pattern in patterns:
        if context:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return int(match.group(1)), "regex"
    
    return None, None

def extract_price_regex(text, context=None):
    """Extract price using regex patterns"""
    context = context or text
    patterns = [
        r'(?:price)\s*[\:\#]?\s*[\$\£\€]?\s*(\d+(?:\.\d{1,2})?)',  # Price: $10.99
        r'[\$\£\€]\s*(\d+(?:\.\d{1,2})?)'  # $10.99
    ]
    
    for pattern in patterns:
        if context:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return float(match.group(1)), "regex"
    
    return None, None

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
    
    # First attempt to extract with regex patterns which are more reliable for formatted data
    # Extract Order ID
    order_id_match = re.search(r'order\s*(?:id|number|#)?\s*[\:\#]?\s*([a-zA-Z0-9\-\_]+)', text, re.IGNORECASE)
    if order_id_match:
        structured_data["order_id"]["value"] = order_id_match.group(1).upper()
        structured_data["order_id"]["confidence"] = 0.95  # High confidence for regex matches
        structured_data["order_id"]["source"] = "regex"
    
    # Extract Customer
    customer_match = re.search(r'customer\s*[\:\#]?\s*([a-zA-Z0-9\s]+(?:$|\n))', text, re.IGNORECASE)
    if customer_match:
        structured_data["customer"]["value"] = customer_match.group(1).strip()
        structured_data["customer"]["confidence"] = 0.95
        structured_data["customer"]["source"] = "regex"
    
    # Extract Shipping Address
    address_match = re.search(r'(?:shipping|delivery)?\s*address\s*[\:\#]?\s*([a-zA-Z0-9\s\,\-\.]+(?:$|\n))', text, re.IGNORECASE)
    if address_match:
        structured_data["shipping_address"]["value"] = address_match.group(1).strip()
        structured_data["shipping_address"]["confidence"] = 0.95
        structured_data["shipping_address"]["source"] = "regex"
    
    # Extract Line Items
    # Look for patterns like: SKU: X123, Quantity: 20, Price: $42.99
    line_item_matches = re.finditer(
        r'(?:sku|item|product)\s*[\:\#]?\s*([a-zA-Z0-9\-\_]+)[^\n]*?'
        r'(?:qty|quantity)\s*[\:\#]?\s*(\d+)[^\n]*?'
        r'(?:price)\s*[\:\#]?\s*[\$\£\€]?\s*(\d+(?:\.\d{1,2})?)',
        text,
        re.IGNORECASE
    )
    
    for match in line_item_matches:
        line_item = {
            "sku": {
                "value": match.group(1),
                "confidence": 0.95,
                "source": "regex"
            },
            "quantity": {
                "value": int(match.group(2)),
                "confidence": 0.95,
                "source": "regex"
            },
            "price": {
                "value": float(match.group(3)),
                "confidence": 0.95,
                "source": "regex"
            }
        }
        
        # Add warnings for low confidence
        if line_item["sku"]["confidence"] < CONFIDENCE_THRESHOLD:
            line_item["sku"]["warning"] = True
        if line_item["quantity"]["confidence"] < CONFIDENCE_THRESHOLD:
            line_item["quantity"]["warning"] = True
        if line_item["price"]["confidence"] < CONFIDENCE_THRESHOLD:
            line_item["price"]["warning"] = True
            
        structured_data["line_items"].append(line_item)
    
    # If no line items found, try a more flexible pattern
    if not structured_data["line_items"]:
        # Try to find SKUs
        sku_matches = re.finditer(r'(?:sku|item|product)\s*[\:\#]?\s*([a-zA-Z0-9\-\_]+)', text, re.IGNORECASE)
        for match in sku_matches:
            sku = match.group(1)
            context = text[match.start():match.start()+200]  # Look at nearby context
            
            # Look for quantity nearby
            qty, qty_source = extract_quantity_regex(context)
            qty = qty if qty is not None else 1
            qty_confidence = 0.8 if qty_source == "regex" else 0.5
            
            # Look for price nearby
            price, price_source = extract_price_regex(context)
            price = price if price is not None else 0.0
            price_confidence = 0.8 if price_source == "regex" else 0.5
            
            line_item = {
                "sku": {
                    "value": sku,
                    "confidence": 0.9,
                    "source": "regex"
                },
                "quantity": {
                    "value": qty,
                    "confidence": qty_confidence,
                    "source": qty_source or "default"
                },
                "price": {
                    "value": price,
                    "confidence": price_confidence,
                    "source": price_source or "default"
                }
            }
            
            # Add warnings for low confidence
            if line_item["sku"]["confidence"] < CONFIDENCE_THRESHOLD:
                line_item["sku"]["warning"] = True
            if line_item["quantity"]["confidence"] < CONFIDENCE_THRESHOLD:
                line_item["quantity"]["warning"] = True
            if line_item["price"]["confidence"] < CONFIDENCE_THRESHOLD:
                line_item["price"]["warning"] = True
                
            structured_data["line_items"].append(line_item)
    
    # If no line items found yet, as a last resort, look for any SKU-like patterns with capitals and numbers
    if not structured_data["line_items"]:
        sku_candidates = re.findall(r'\b([A-Z][A-Z0-9\-\_]{2,})\b', text)
        for sku in sku_candidates:
            # Look for nearby numbers that could be quantities
            idx = text.find(sku)
            if idx >= 0:
                context = text[idx:idx+100]
                
                qty, qty_source = extract_quantity_regex(context)
                qty = qty if qty is not None else 1
                qty_confidence = 0.7 if qty_source == "regex" else 0.4
                
                price, price_source = extract_price_regex(context)
                price = price if price is not None else 0.0
                price_confidence = 0.7 if price_source == "regex" else 0.4
                
                line_item = {
                    "sku": {
                        "value": sku,
                        "confidence": 0.7,
                        "source": "pattern"
                    },
                    "quantity": {
                        "value": qty,
                        "confidence": qty_confidence,
                        "source": qty_source or "default"
                    },
                    "price": {
                        "value": price,
                        "confidence": price_confidence,
                        "source": price_source or "default"
                    }
                }
                
                # Add warnings for low confidence
                if line_item["sku"]["confidence"] < CONFIDENCE_THRESHOLD:
                    line_item["sku"]["warning"] = True
                if line_item["quantity"]["confidence"] < CONFIDENCE_THRESHOLD:
                    line_item["quantity"]["warning"] = True
                if line_item["price"]["confidence"] < CONFIDENCE_THRESHOLD:
                    line_item["price"]["warning"] = True
                    
                structured_data["line_items"].append(line_item)
    
    # Only proceed with NER if regex didn't find everything
    if not (structured_data["customer"]["value"] and structured_data["order_id"]["value"] and 
            structured_data["shipping_address"]["value"] and structured_data["line_items"]):
        
        # Clean the text
        cleaned_text = clean_text(text)
        
        # Get entity predictions with confidence
        entity_pairs = predict_entities(cleaned_text)
        
        # Group consecutive tokens of the same entity type
        grouped_entities = group_entities(entity_pairs)
        
        # Process grouped entities
        current_line_item = {}
        
        for entity in grouped_entities:
            entity_text, entity_type = entity[0], entity[1]
            confidence = entity[2] if len(entity) > 2 else 0.7  # Default confidence if not provided
            
            # Map entity types to our structured fields
            if entity_type == "PER" or entity_type == "ORG":
                if not structured_data["customer"]["value"]:
                    structured_data["customer"]["value"] = entity_text
                    structured_data["customer"]["confidence"] = confidence
                    structured_data["customer"]["source"] = "ner"
                    if confidence < CONFIDENCE_THRESHOLD:
                        structured_data["customer"]["warning"] = True
            elif entity_type == "MISC" and "order" in entity_text.lower():
                # Extract order ID using regex
                order_match = re.search(r'order\s*(?:id|number)?\s*[\:\#]?\s*([a-z0-9\-]+)', 
                                       entity_text.lower())
                if order_match and not structured_data["order_id"]["value"]:
                    structured_data["order_id"]["value"] = order_match.group(1).upper()
                    structured_data["order_id"]["confidence"] = confidence * 0.9  # Slightly reduce confidence due to regex extraction
                    structured_data["order_id"]["source"] = "ner+regex"
                    if confidence * 0.9 < CONFIDENCE_THRESHOLD:
                        structured_data["order_id"]["warning"] = True
            elif entity_type == "LOC":
                if not structured_data["shipping_address"]["value"]:
                    structured_data["shipping_address"]["value"] = entity_text
                    structured_data["shipping_address"]["confidence"] = confidence
                    structured_data["shipping_address"]["source"] = "ner"
                elif structured_data["shipping_address"]["value"]:
                    structured_data["shipping_address"]["value"] += ", " + entity_text
                    # Average the confidence
                    structured_data["shipping_address"]["confidence"] = (
                        structured_data["shipping_address"]["confidence"] + confidence
                    ) / 2
                    if confidence < CONFIDENCE_THRESHOLD:
                        structured_data["shipping_address"]["warning"] = True
            elif entity_type == "PRODUCT" or entity_type == "MISC" and re.search(r'[A-Z0-9]{3,}', entity_text):
                # Product or SKU
                if current_line_item and "quantity" in current_line_item:
                    # Save previous line item if we have one with a quantity
                    if current_line_item not in structured_data["line_items"]:
                        structured_data["line_items"].append(current_line_item)
                    current_line_item = {}
                
                current_line_item = {
                    "sku": {
                        "value": entity_text,
                        "confidence": confidence,
                        "source": "ner"
                    }
                }
                if confidence < CONFIDENCE_THRESHOLD:
                    current_line_item["sku"]["warning"] = True
            elif entity_type == "CARDINAL" or entity_type == "QUANTITY":
                # Try to parse as a quantity
                qty_match = re.search(r'(\d+)', entity_text)
                if qty_match and current_line_item and "sku" in current_line_item:
                    current_line_item["quantity"] = {
                        "value": int(qty_match.group(1)),
                        "confidence": confidence,
                        "source": "ner"
                    }
                    if confidence < CONFIDENCE_THRESHOLD:
                        current_line_item["quantity"]["warning"] = True
            elif entity_type == "MONEY" or entity_type == "PRICE":
                # Try to parse as price
                price_match = re.search(r'[\$\£\€]?\s*(\d+(?:\.\d{1,2})?)', entity_text)
                if price_match and current_line_item and "sku" in current_line_item:
                    current_line_item["price"] = {
                        "value": float(price_match.group(1)),
                        "confidence": confidence,
                        "source": "ner"
                    }
                    if confidence < CONFIDENCE_THRESHOLD:
                        current_line_item["price"]["warning"] = True
                    
                    # Complete line item and add to list
                    if "quantity" not in current_line_item:
                        current_line_item["quantity"] = {
                            "value": 1,
                            "confidence": 0.5,
                            "source": "default",
                            "warning": True
                        }
                    if current_line_item not in structured_data["line_items"]:
                        structured_data["line_items"].append(current_line_item)
                    current_line_item = {}
        
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
    
    # If we still don't have any fields, try regex extraction again with lower confidence
    if not structured_data["order_id"]["value"]:
        order_id, source = extract_sku_regex(text)
        if order_id:
            structured_data["order_id"]["value"] = order_id.upper()
            structured_data["order_id"]["confidence"] = 0.6
            structured_data["order_id"]["source"] = source
            structured_data["order_id"]["warning"] = True
    
    return structured_data

def parse_order_document(text):
    """
    Main function to parse an order document text.
    
    Args:
        text (str): Raw text from a document
        
    Returns:
        dict: Structured order data
    """
    # Extract structured data from text
    structured_data = extract_entities(text)
    
    # Flatten the output for backward compatibility
    flat_output = {
        "customer": structured_data["customer"]["value"],
        "order_id": structured_data["order_id"]["value"],
        "shipping_address": structured_data["shipping_address"]["value"],
        "line_items": []
    }
    
    # Flatten line items
    for item in structured_data["line_items"]:
        flat_item = {
            "sku": item["sku"]["value"],
            "quantity": item["quantity"]["value"],
            "price": item["price"]["value"]
        }
        flat_output["line_items"].append(flat_item)
    
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
    
    return flat_output 