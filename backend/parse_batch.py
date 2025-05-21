#!/usr/bin/env python3
"""
Batch processing script for document parsing with LLM fallback support.
This script processes multiple documents from a directory and outputs the results.
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import document extraction and parsing functions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils import extract_text
from app.parser_v2 import parse_order_document

def process_file(file_path, output_dir, use_llm=False, dry_run=False):
    """
    Process a single document file and save the results
    
    Args:
        file_path (str): Path to the document file
        output_dir (str): Directory to save results
        use_llm (bool): Whether to force LLM parser or use auto-fallback
        dry_run (bool): If True, don't save results
        
    Returns:
        dict: Processing result information
    """
    filename = os.path.basename(file_path)
    logger.info(f"Processing file: {filename}")
    
    # Set environment variable for LLM use if needed
    if use_llm:
        os.environ["USE_LLM_PARSER"] = "true"
        logger.info("LLM parser forced ON")
    else:
        os.environ.pop("USE_LLM_PARSER", None)
        logger.info("Using NER with LLM fallback")
    
    try:
        # Extract text from file
        extraction_result = extract_text(file_path)
        
        if not extraction_result['success']:
            logger.error(f"Text extraction failed for {filename}: {extraction_result.get('error', 'Unknown error')}")
            return {
                "file": filename,
                "success": False,
                "error": extraction_result.get('error', 'Text extraction failed')
            }
        
        # Parse the document
        start_time = time.time()
        parsed_data = parse_order_document(extraction_result['text'])
        processing_time = time.time() - start_time
        
        # Determine which parser was used based on the source field
        parser_used = parsed_data.get('source', 'unknown')
        confidence = parsed_data.get('confidence', {}).get('overall', 0)
        
        # Save results
        if not dry_run:
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, 'w') as f:
                json.dump(parsed_data, f, indent=2)
            logger.info(f"Results saved to {output_path}")
        
        return {
            "file": filename,
            "success": True,
            "parser_used": parser_used,
            "confidence": confidence,
            "processing_time": processing_time,
            "output_path": None if dry_run else os.path.join(output_dir, output_filename)
        }
        
    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        return {
            "file": filename,
            "success": False,
            "error": str(e)
        }

def batch_process(input_dir, output_dir, file_patterns=None, use_llm=False, dry_run=False, delay=0):
    """
    Process multiple documents from a directory
    
    Args:
        input_dir (str): Input directory containing documents
        output_dir (str): Output directory for parsed results
        file_patterns (list): List of file patterns to process (e.g. ['.pdf', '.txt'])
        use_llm (bool): Whether to force LLM parser
        dry_run (bool): If True, don't save results
        delay (int): Delay in seconds between processing files (for API rate limits)
        
    Returns:
        list: Processing results for all files
    """
    # Create output directory if it doesn't exist
    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)
    
    # Get list of files to process
    files = []
    input_path = Path(input_dir)
    
    if file_patterns:
        for pattern in file_patterns:
            files.extend(list(input_path.glob(f"*{pattern}")))
    else:
        # Default file types
        for ext in ['.pdf', '.txt', '.png', '.jpg', '.jpeg']:
            files.extend(list(input_path.glob(f"*{ext}")))
    
    if not files:
        logger.warning(f"No matching files found in {input_dir}")
        return []
    
    logger.info(f"Found {len(files)} files to process")
    
    # Process each file
    results = []
    for i, file_path in enumerate(files):
        logger.info(f"Processing file {i+1}/{len(files)}: {file_path.name}")
        result = process_file(str(file_path), output_dir, use_llm, dry_run)
        results.append(result)
        
        # Print result summary
        if result["success"]:
            parser = result["parser_used"]
            confidence = result.get("confidence", 0)
            logger.info(f"✅ Success: {file_path.name} (Parser: {parser}, Confidence: {confidence:.2f})")
        else:
            logger.error(f"❌ Failed: {file_path.name} - {result.get('error', 'Unknown error')}")
        
        # Delay between files (for API rate limiting)
        if delay > 0 and i < len(files) - 1:  # No need to delay after the last file
            logger.info(f"Waiting {delay} seconds before next file...")
            time.sleep(delay)
    
    # Print summary statistics
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    ner_used = sum(1 for r in results if r.get("success") and r.get("parser_used") == "ner")
    llm_used = sum(1 for r in results if r.get("success") and r.get("parser_used") == "llm")
    
    logger.info("\n===== BATCH PROCESSING SUMMARY =====")
    logger.info(f"Total files processed: {len(results)}")
    logger.info(f"Successful: {successful}, Failed: {failed}")
    logger.info(f"NER parser used: {ner_used}, LLM parser used: {llm_used}")
    
    return results

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Batch process document files with parser")
    parser.add_argument("--input-dir", required=True, help="Directory containing documents to process")
    parser.add_argument("--output-dir", default="./results", help="Directory to save results (default: ./results)")
    parser.add_argument("--patterns", nargs="+", help="File patterns to process (e.g. .pdf .txt)")
    parser.add_argument("--use-llm", action="store_true", help="Force LLM parser for all documents")
    parser.add_argument("--dry-run", action="store_true", help="Don't save results, just process")
    parser.add_argument("--delay", type=int, default=0, help="Delay in seconds between files (for API rate limits)")
    
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    if not os.environ.get("OPENAI_API_KEY") and (args.use_llm or not args.dry_run):
        logger.warning("OPENAI_API_KEY not set in environment. LLM fallback will not work.")
    
    # Process documents
    batch_process(
        args.input_dir, 
        args.output_dir, 
        args.patterns, 
        args.use_llm, 
        args.dry_run, 
        args.delay
    )

if __name__ == "__main__":
    main() 