# LLM Fallback Parser for Document Processing

This module provides an AI-powered fallback parsing system using OpenAI's GPT-3.5 Turbo model. The LLM (Large Language Model) parser enhances the accuracy of document extraction for complex or non-standard order documents.

## Quick Start

1. Ensure your OpenAI API key is set in your environment:

```bash
export OPENAI_API_KEY=your_openai_api_key
```

2. The LLM parser is enabled by default with the following settings:

```bash
USE_LLM_PARSER=true
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1000
```

3. To disable the LLM parser and use only the traditional parser:

```bash
USE_LLM_PARSER=false
```

## Overview

The LLM fallback parser is designed to enhance the reliability of document parsing by using a large language model (like OpenAI's GPT models) when the traditional NER+regex extraction has low confidence. The system will:

1. First attempt to parse a document using the established NER and regex-based methods
2. Check the overall confidence score of the extraction
3. If the confidence is below a threshold (default 0.6), the system falls back to using an LLM for extraction
4. The LLM-extracted data is structured in the same format as the standard parser output

## Quick Setup

For the fastest setup, run this PowerShell script:

```powershell
.\setup_llm.ps1
```

This will:
1. Install required packages
2. Set up the `.env` file with your API key
3. Test the LLM parser with a sample document

## Manual Setup

### Setting up OpenAI API Key

To use the LLM fallback parser, you need an OpenAI API key:

1. Sign up at https://platform.openai.com/ 
2. Create an API key in your account dashboard
3. Create a `.env` file in the backend directory with:
   ```
   OPENAI_API_KEY=your_api_key_here
   USE_LLM_PARSER=true
   ```

### Validation and Testing

After setting up your API key:

1. Run `python check_env.py` to validate your environment setup
2. Run `python test_llm_directly.py` to test with a sample document 

## Configuration

The LLM fallback parser is controlled by the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Required OpenAI API key |
| `USE_LLM_PARSER` | true | Set to `true` to always use LLM parser |
| `LLM_MODEL` | gpt-3.5-turbo | OpenAI model to use (gpt-3.5-turbo recommended) |
| `LLM_TEMPERATURE` | 0.2 | Temperature setting for LLM (lower is more deterministic) |
| `LLM_MAX_TOKENS` | 1000 | Maximum number of tokens in LLM response |
| `LLM_BASE_CONFIDENCE` | 0.8 | Base confidence level for LLM results (adjusted dynamically) |
| `CONFIDENCE_THRESHOLD` | 0.6 | Threshold below which to use LLM fallback (when `USE_LLM_PARSER=false`) |

## Rate Limiting and Error Handling

The LLM fallback parser includes robust rate limiting and error handling:

1. **Automatic Retry Logic**: When rate limits are hit, the system automatically retries with exponential backoff.
2. **Graceful Fallbacks**: If the OpenAI API is unavailable or returns errors, the system falls back to the standard parser results.
3. **Batch Processing**: For large document sets, use the batch processor to handle rate limits:
   ```
   python batch_process.py data/documents --delay 10
   ```
   This processes files with a configurable delay between each to avoid hitting rate limits.

## Troubleshooting

If the LLM fallback parser isn't working:

1. **Check API Key**: Make sure your OpenAI API key is valid and properly set in `.env`
2. **Internet Connection**: Verify your server has internet access to reach the OpenAI API
3. **Package Installation**: Ensure `requests` and `python-dotenv` are installed
4. **Environment Loading**: Check if `.env` is being loaded correctly
5. **Log Files**: Check the application logs for specific error messages
6. **Rate Limits**: If you're seeing 429 errors, you might be exceeding your OpenAI API quota. Use batch processing with longer delays.

Run the diagnostic script to identify issues:
```
python check_env.py
```

## Integration Details

The LLM fallback is triggered in two ways:

1. **Low Confidence**: When the standard parser returns confidence below the threshold
2. **Forced Mode**: When `USE_LLM_PARSER=true` is set in the environment

The result from the LLM is processed to match the expected output format and assigned confidence scores.

## How It Works

The LLM fallback mechanism works as follows:

1. When a document is processed, it's first analyzed using the normal NER+regex extraction pipeline
2. The system calculates an overall confidence score for the extraction
3. If the confidence is below the threshold (default 0.6), the text is sent to the LLM
4. The LLM extracts structured data following a detailed prompt
5. The result is converted to the same format used by the standard parser
6. If the LLM fails for any reason, the system falls back to the original extraction

## Logging

The system logs when the LLM fallback parser is used:

```
INFO - LLM fallback parser used due to low confidence: 0.45 (threshold: 0.6)
```

## Testing

You can force the use of the LLM parser for testing by setting:

```
USE_LLM_PARSER=true
```

in your `.env` file or as an environment variable.

## Prompt Template

The LLM parser uses a carefully crafted prompt template designed to extract structured data from raw document text. The prompt:

1. Instructs the model to extract order_id, customer, shipping_address, and line_items
2. Provides rules for handling specific edge cases like SKU validation
3. Shows examples of both input and expected output formats
4. Forces the model to return a clean JSON object without additional text

## Dependencies

This feature requires the following Python packages:

- `requests`: For making API calls to OpenAI
- `python-dotenv`: For loading environment variables from .env files

These are included in the updated requirements.txt file.

## Operation Modes

The LLM parser operates in two modes:

1. **Default Mode**: By default, the system now uses the LLM parser (`USE_LLM_PARSER=true`). This provides the highest accuracy for document parsing as it leverages the full capabilities of GPT-3.5 Turbo.

2. **Fallback Mode**: When `USE_LLM_PARSER=false`, the system first attempts to parse documents using the traditional NER+regex approach. If the confidence score is below the `CONFIDENCE_THRESHOLD` (default: 0.6), it will fall back to the LLM parser.

The system is now optimized for better accuracy with rate limiting protection built in.

## Usage Examples

### Using the Default LLM Parser (Recommended)

By default, all documents are processed using the LLM parser:

```bash
export OPENAI_API_KEY=your_openai_api_key
python run.py
```

### Using Traditional Parser with LLM Fallback

To use the traditional parser first and fall back to LLM only when needed:

```bash
export OPENAI_API_KEY=your_openai_api_key
export USE_LLM_PARSER=false
export CONFIDENCE_THRESHOLD=0.6
python run.py
```

### Batch Processing with Rate Limit Management

For processing multiple documents with rate limit awareness:

```bash
export OPENAI_API_KEY=your_openai_api_key
python batch_process.py --input-dir path/to/documents --output-dir path/to/results --delay 3
```

## Operational Flow

The document parsing system now follows this updated flow:

1. Document is uploaded and preprocessed with OCR if needed
2. Text extraction is performed on the document
3. **LLM Parsing**: The GPT-3.5 Turbo model is used to extract structured data from the document text (since `USE_LLM_PARSER=true` by default)
4. If the LLM parser encounters rate limits or errors:
   - The system automatically retries with exponential backoff
   - If still failing, it falls back to the traditional parser
5. The parsed data is structured and returned

If you switch to fallback mode (`USE_LLM_PARSER=false`), the flow becomes:

1. Document is uploaded and preprocessed
2. Text extraction is performed
3. **Traditional Parsing**: NER and regex rules attempt to extract structured data
4. The system calculates a confidence score for the extraction
5. If confidence < `CONFIDENCE_THRESHOLD`, the LLM parser is used as fallback
6. The highest confidence result is returned 

## Testing the GPT-3.5 Turbo Integration

A test script has been provided to verify the integration with GPT-3.5 Turbo:

```bash
python test_gpt35.py
```

This script will:
1. Load your environment configuration
2. Display the current LLM settings
3. Process a sample document using the GPT-3.5 Turbo parser
4. Output the parsing results and verify key fields

If you encounter rate limit errors during testing, the system will automatically retry with exponential backoff. In a production setting, you can adjust the delay between document processing using the batch processing script:

```bash
python batch_process.py --input-dir ./test_docs --output-dir ./results --delay 10
```

The `--delay` parameter sets the pause between API calls in seconds, helping to avoid rate limit errors. 