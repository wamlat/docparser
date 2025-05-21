#!/usr/bin/env python3
"""
Batch Processor for Document Parsing with Rate Limiting

This script processes documents in batches with deliberate delays to avoid OpenAI API rate limits.
It's useful for processing multiple documents when you know the LLM fallback will be used.
"""

import os
import time
import glob
import argparse
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set USE_LLM_PARSER to True to force LLM usage
os.environ["USE_LLM_PARSER"] = "true"

def process_file(file_path):
    """Process a single file using the document parser"""
    try:
        # Import only when needed to ensure environment variables are loaded first
        from app.parser_v2 import parse_order_document
        from app.ocr import extract_text_from_file
        
        logger.info(f"Processing file: {file_path}")
        
        # Extract text from file
        text = extract_text_from_file(file_path)
        if not text:
            logger.error(f"Failed to extract text from {file_path}")
            return None
            
        # Parse the document
        result = parse_order_document(text)
        
        logger.info(f"Successfully processed {file_path}")
        
        # Check if LLM was actually used
        if result.get("source") == "llm":
            logger.info(f"LLM was used for processing {file_path}")
            
        return result
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return None

def batch_process(directory, pattern="*.pdf", delay=5):
    """
    Process all matching files in a directory with a delay between each
    to avoid OpenAI API rate limits
    
    Args:
        directory (str): Directory containing files to process
        pattern (str): Glob pattern to match files
        delay (int): Delay in seconds between processing each file
    """
    # Find all matching files
    file_paths = glob.glob(os.path.join(directory, pattern))
    
    if not file_paths:
        logger.warning(f"No files matching '{pattern}' found in {directory}")
        return []
    
    logger.info(f"Found {len(file_paths)} files to process")
    
    results = []
    for i, file_path in enumerate(file_paths):
        logger.info(f"Processing file {i+1}/{len(file_paths)}: {file_path}")
        
        result = process_file(file_path)
        results.append({"file": file_path, "result": result})
        
        # Add delay between files to avoid rate limits (except for the last file)
        if i < len(file_paths) - 1:
            logger.info(f"Waiting {delay} seconds before processing next file...")
            time.sleep(delay)
    
    return results

def save_results(results, output_file="batch_results.txt"):
    """Save results to a file"""
    with open(output_file, "w") as f:
        for item in results:
            f.write(f"File: {item['file']}\n")
            if item['result']:
                f.write(f"  Order ID: {item['result'].get('order_id', 'Not found')}\n")
                f.write(f"  Customer: {item['result'].get('customer', 'Not found')}\n")
                f.write(f"  Line Items: {len(item['result'].get('line_items', []))}\n")
                
                # Print confidence scores if available
                if 'confidence' in item['result']:
                    f.write(f"  Confidence: {item['result']['confidence'].get('overall', 0):.2f}\n")
                    
                # Check source
                if item['result'].get('source') == 'llm':
                    f.write("  Source: LLM\n")
                else:
                    f.write("  Source: Standard Parser\n")
            else:
                f.write("  Failed to process\n")
            f.write("\n")
    
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process documents with rate limiting")
    parser.add_argument("directory", help="Directory containing files to process")
    parser.add_argument("--pattern", default="*.pdf", help="File pattern to match")
    parser.add_argument("--delay", type=int, default=5, help="Delay between processing files (seconds)")
    parser.add_argument("--output", default="batch_results.txt", help="Output file for results")
    
    args = parser.parse_args()
    
    # Process files
    results = batch_process(args.directory, args.pattern, args.delay)
    
    # Save results
    save_results(results, args.output) 