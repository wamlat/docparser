# Document Parser

An intelligent document parsing system for extracting structured information from orders, invoices, and shipping documents.

## Overview

The Document Parser uses a combination of NER (Named Entity Recognition), regex pattern matching, and LLM (Large Language Model) technologies to extract structured data from business documents with high accuracy.

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   cp env.sample .env
   # Update .env with your settings and API keys
   ```

## Features

- Extract structured data from PDFs, text files, and images
- Named Entity Recognition (NER) using BERT models
- Large Language Model (LLM) fallback for complex documents
- Support for batch processing of multiple documents
- RESTful API for integration with other systems
- Web UI for manual document processing

## LLM Fallback Parser

If the standard parser detects low confidence (<0.6 by default), it automatically switches to a large language model (LLM) to extract structured data using GPT-3.5 Turbo. The LLM parser can handle:

- Ambiguous formatting
- Non-standard document layouts
- Complex multi-line items
- Incomplete or partial information

The LLM parser works by:
1. Sending the document text to the OpenAI API
2. Using a tailored prompt to extract structured JSON
3. Processing the response into the same format as the standard parser

This hybrid approach combines the speed of NER+regex for standard documents with the intelligence of GPT models for complex edge cases, ensuring high accuracy across a wide range of document formats.

You can also force the system to always use the LLM parser by setting `USE_LLM_PARSER=true` in your environment variables or using the UI toggle in the web interface.

See [README_LLM_FALLBACK.md](./README_LLM_FALLBACK.md) for detailed configuration options and usage examples.

## API Documentation

The system exposes a RESTful API for document processing:

- `POST /upload` - Upload a document file for processing
- `GET /parse` - Extract structured data from the uploaded document
- `GET /stats` - Get parser usage statistics
- `GET /download` - Download the processed results as JSON

## Development

For development setup and contributing guidelines, see [CONTRIBUTING.md](./CONTRIBUTING.md). 