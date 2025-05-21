import os
import json
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default flag to control when LLM parsing is used
# Can be overridden by environment variable
USE_LLM_PARSER = os.environ.get("USE_LLM_PARSER", "True").lower() in ("true", "1", "yes")

# Get API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Define the OpenAI API endpoint for completions
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# LLM model configuration
DEFAULT_MODEL = "gpt-3.5-turbo"
LLM_MODEL = os.environ.get("LLM_MODEL", DEFAULT_MODEL)
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "1000"))

# Base LLM confidence that will be adjusted dynamically
LLM_BASE_CONFIDENCE = float(os.environ.get("LLM_BASE_CONFIDENCE", "0.8"))

def get_prompt_template():
    """
    Returns the prompt template for extracting order information from text.
    """
    return """
You are a specialized system designed to extract structured order information from order document text.
Extract the following fields from the text:
- order_id: The unique identifier of the order, usually labeled "Order ID", "Order Number", "PO #", etc.
- customer: The name of the customer or company placing the order
- shipping_address: The complete shipping address
- line_items: An array of products being ordered, each with:
  - sku: The product SKU or item number
  - quantity: The quantity ordered
  - price: The unit price (numeric value only)

Return ONLY a JSON object with these fields. Do not include any explanations or additional text.

Some important rules:
1. Make sure SKUs are valid product codes (usually containing letters and numbers, like "ABC-123"), not just single letters or generic words.
2. Remove any line items with generic SKUs like "s", "x", or single digits.
3. Don't include section headers like "Line Items:" in the shipping address.
4. Remove any non-address information from shipping_address like "Thanks" or "Reference".
5. Only include shipping address lines that start with capital letters or numbers (proper address format).
6. Prices should be numeric values without currency symbols.

Example input:
```
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
```

Example output:
```json
{
  "order_id": "PO-12345",
  "customer": "Acme Corporation",
  "shipping_address": "123 Main Street, Suite 100, San Francisco, CA 94105",
  "line_items": [
    {"sku": "HTP-2000", "quantity": 5, "price": 125.0},
    {"sku": "LMN-300X", "quantity": 2, "price": 45.5}
  ]
}
```

TEXT TO EXTRACT FROM:
"""

def parse_with_llm(text: str) -> dict:
    """
    Process the text using an LLM to extract structured order information.
    
    Args:
        text (str): The raw text extracted from an order document
        
    Returns:
        dict: Structured order data in the same format as parse_order_document output
    """
    # Log when LLM fallback parser is used
    logger.info("Using LLM fallback parser")
    
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not set. Set the OPENAI_API_KEY environment variable.")
        return create_empty_result_with_error("OpenAI API key not configured")
    
    # Create prompt with template + text
    prompt = get_prompt_template() + text
    
    # Retry parameters
    max_retries = 3
    retry_delay = 2  # Initial delay in seconds
    
    for attempt in range(max_retries):
        try:
            # Call OpenAI API
            response = requests.post(
                OPENAI_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a specialized order document parser that extracts structured information from raw document text."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                },
                timeout=30  # 30 second timeout
            )
            
            # Handle rate limit errors with retries
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit. Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} attempts")
                    return create_empty_result_with_error(f"OpenAI API rate limit exceeded after {max_retries} attempts")
            
            # Check response for other errors
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            if "choices" not in result or not result["choices"]:
                logger.error("Unexpected API response format: %s", result)
                return create_empty_result_with_error("Unexpected API response format")
            
            # Extract content from response
            content = result["choices"][0]["message"]["content"]
            
            # Sometimes the API returns content with ```json at start and ``` at end
            if content.startswith('```json'):
                content = content.split('```json', 1)[1]
            if '```' in content:
                content = content.split('```', 1)[0]
            
            content = content.strip()
            
            try:
                # Parse the JSON content
                parsed_data = json.loads(content)
                
                # Create structured result with confidence scores
                structured_result = create_structured_result(parsed_data)
                
                # Log success
                logger.info("LLM parsing successful with overall confidence %s", 
                            structured_result.get("confidence", {}).get("overall", 0))
                
                return structured_result
                
            except json.JSONDecodeError as e:
                logger.error("Failed to parse LLM response as JSON: %s\nContent: %s", str(e), content)
                return create_empty_result_with_error(f"Failed to parse LLM response as JSON: {str(e)}")
            
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"API request error: {str(e)}. Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                import time
                time.sleep(wait_time)
            else:
                logger.error(f"API request error after {max_retries} attempts: {str(e)}")
                return create_empty_result_with_error(f"API request error after {max_retries} attempts: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error in LLM parsing: %s", str(e))
            return create_empty_result_with_error(f"Unexpected error in LLM parsing: {str(e)}")

def create_empty_result_with_error(error_message):
    """Create an empty result structure with an error message"""
    result = {
        "customer": "",
        "order_id": "",
        "shipping_address": "",
        "line_items": [],
        "confidence": {
            "customer": 0,
            "order_id": 0,
            "shipping_address": 0,
            "line_items": 0,
            "overall": 0
        },
        "extraction_details": {
            "customer": {"value": "", "confidence": 0, "source": "llm"},
            "order_id": {"value": "", "confidence": 0, "source": "llm"},
            "shipping_address": {"value": "", "confidence": 0, "source": "llm"},
            "line_items": []
        },
        "error": error_message
    }
    return result

def calculate_dynamic_confidence(model, has_order_id, has_customer, has_address, line_items_count):
    """
    Calculate a dynamic confidence score based on the quality and completeness of the extracted data
    
    Args:
        model (str): The LLM model used
        has_order_id (bool): Whether an order ID was extracted
        has_customer (bool): Whether a customer name was extracted
        has_address (bool): Whether a shipping address was extracted
        line_items_count (int): Number of line items extracted
        
    Returns:
        float: A confidence score between 0.7 and 0.95
    """
    # Start with base confidence
    confidence = LLM_BASE_CONFIDENCE
    
    # Adjust based on model - GPT-4 is generally more accurate than GPT-3.5
    if "gpt-4" in model.lower():
        confidence += 0.05
    
    # Adjust based on completeness - essential fields
    completeness_score = 0
    if has_order_id:
        completeness_score += 0.3
    if has_customer:
        completeness_score += 0.2
    if has_address:
        completeness_score += 0.2
    
    # Adjust based on line items found
    if line_items_count > 0:
        # More line items generally indicate better extraction
        completeness_score += min(0.3, line_items_count * 0.05)
    
    # Apply completeness adjustment (normalized)
    confidence += (completeness_score / 10)
    
    # Ensure confidence stays in reasonable bounds (0.7 to 0.95)
    return max(0.7, min(0.95, confidence))

def create_structured_result(parsed_data):
    """
    Convert the raw parsed data from LLM into the structured format expected by the application.
    Assigns confidence scores to the LLM results.
    """
    # Calculate dynamic confidence based on extracted content quality
    has_order_id = bool(parsed_data.get("order_id", ""))
    has_customer = bool(parsed_data.get("customer", ""))
    has_address = bool(parsed_data.get("shipping_address", ""))
    line_items_count = len(parsed_data.get("line_items", []))
    
    # Get dynamic confidence value
    dynamic_confidence = calculate_dynamic_confidence(
        LLM_MODEL, 
        has_order_id,
        has_customer,
        has_address,
        line_items_count
    )
    
    # Create the basic structure
    structured_result = {
        "customer": parsed_data.get("customer", ""),
        "order_id": parsed_data.get("order_id", ""),
        "shipping_address": parsed_data.get("shipping_address", ""),
        "line_items": [],
        "confidence": {
            "customer": dynamic_confidence if parsed_data.get("customer") else 0,
            "order_id": dynamic_confidence if parsed_data.get("order_id") else 0,
            "shipping_address": dynamic_confidence if parsed_data.get("shipping_address") else 0,
            "line_items": 0,
            "overall": 0
        },
        "extraction_details": {
            "customer": {
                "value": parsed_data.get("customer", ""),
                "confidence": dynamic_confidence if parsed_data.get("customer") else 0,
                "source": "llm"
            },
            "order_id": {
                "value": parsed_data.get("order_id", ""),
                "confidence": dynamic_confidence if parsed_data.get("order_id") else 0,
                "source": "llm"
            },
            "shipping_address": {
                "value": parsed_data.get("shipping_address", ""),
                "confidence": dynamic_confidence if parsed_data.get("shipping_address") else 0,
                "source": "llm"
            },
            "line_items": []
        },
        # Add explicit source marker for the overall result
        "source": "llm"
    }
    
    # Process line items
    line_items_confidence = 0
    line_items = parsed_data.get("line_items", [])
    
    if line_items:
        for item in line_items:
            # Create flattened line item
            flat_item = {
                "sku": item.get("sku", ""),
                "quantity": item.get("quantity", 0),
                "price": item.get("price", 0)
            }
            
            # Create detailed line item for extraction_details
            detailed_item = {
                "sku": {"value": item.get("sku", ""), "confidence": dynamic_confidence, "source": "llm"},
                "quantity": {"value": item.get("quantity", 0), "confidence": dynamic_confidence, "source": "llm"},
                "price": {"value": item.get("price", 0), "confidence": dynamic_confidence, "source": "llm"}
            }
            
            # Add items to respective lists
            structured_result["line_items"].append(flat_item)
            structured_result["extraction_details"]["line_items"].append(detailed_item)
            
            # Increment confidence
            line_items_confidence += dynamic_confidence
    
    # Calculate final line items confidence
    if line_items:
        structured_result["confidence"]["line_items"] = line_items_confidence / len(line_items)
    
    # Calculate overall confidence with weighted approach
    # Fields importance: order_id > line_items > customer > shipping_address
    weights = {
        "order_id": 1.5,
        "line_items": 1.3,
        "customer": 1.0,
        "shipping_address": 0.8
    }
    
    confidence_values = {
        "order_id": structured_result["confidence"]["order_id"],
        "line_items": structured_result["confidence"]["line_items"],
        "customer": structured_result["confidence"]["customer"],
        "shipping_address": structured_result["confidence"]["shipping_address"]
    }
    
    # Calculate weighted confidence
    weighted_sum = sum(confidence_values[field] * weights[field] for field in confidence_values)
    total_weight = sum(weights.values())
    
    # Adjust confidence based on completeness
    completeness_factor = sum(1 for field in confidence_values if confidence_values[field] > 0.6) / len(confidence_values)
    
    # Calculate final overall confidence
    if sum(weights.values()) > 0:
        structured_result["confidence"]["overall"] = (weighted_sum / total_weight) * (0.7 + (completeness_factor * 0.3))
    
    return structured_result 