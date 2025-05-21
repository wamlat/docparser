# Document Parser Launch Checklist

This checklist covers everything you need to know to get the document parser up and running, including configuration options and limitations.

## Setup

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd docparser
   ```

2. **Install dependencies**:
   ```
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```
   cp env.sample .env
   # Edit .env to add your OpenAI API key
   ```

4. **Run the server**:
   ```
   cd backend
   python run.py
   ```

5. **Start the frontend** (in a separate terminal):
   ```
   cd frontend
   npm install
   npm run dev
   ```

## Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | **REQUIRED**: Your OpenAI API key for LLM parsing | None |
| `USE_LLM_PARSER` | Whether to use LLM for all documents | `true` |
| `LLM_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |
| `LLM_TEMPERATURE` | Temperature for LLM responses | `0.2` |
| `LLM_MAX_TOKENS` | Maximum tokens for LLM responses | `1000` |
| `LLM_CONFIDENCE` | Confidence level assigned to LLM results | `0.85` |
| `CONFIDENCE_THRESHOLD` | Threshold below which to use LLM fallback | `0.6` |

## Known Limitations

1. **API Rate Limits**: OpenAI has rate limits that may cause `429 Too Many Requests` errors during heavy use.
   - **Solution**: Use the batch processor with delays between documents (`python parse_batch.py --input-dir ./docs --delay 5`)

2. **Document Format Limitations**:
   - PDF files must be text-based (not scanned images)
   - Image files require OCR processing which may be less accurate
   - Text files must be properly formatted with clear sections

3. **Line Items Extraction**: The system may occasionally miss line items or combine them incorrectly.
   - Using `USE_LLM_PARSER=true` typically improves line item extraction

4. **Long Documents**: Documents with many pages may be truncated due to model context limits.
   - GPT-3.5 Turbo has a 4096 token context limit

## Example Test Documents

The repository includes several test documents in the `backend/test_docs/` directory:

1. `Order_1_NovaTech.pdf` - Standard order form with clear sections (high accuracy expected)
2. `Order_2_Complex.pdf` - Complex order with multiple line items (medium accuracy expected)
3. `Order_3_Ambiguous.txt` - Text-only order with ambiguous formatting (LLM fallback recommended)

To test with these documents:
```
python parse_batch.py --input-dir ./test_docs --output-dir ./results
```

## Switching Between NER and LLM

There are multiple ways to control which parser is used:

### Environment Variable Method

Edit your `.env` file:
```
# Always use LLM for all documents
USE_LLM_PARSER=true

# OR use NER with LLM fallback for low confidence
USE_LLM_PARSER=false
CONFIDENCE_THRESHOLD=0.6
```

### UI Toggle Method

The web interface includes an "LLM Mode" toggle switch that controls whether the system uses:
- LLM parser for all documents (ON)
- NER with LLM fallback (OFF)

### API Parameter Method

When calling the API directly, add the `llm=true` query parameter:
```
GET /parse?llm=true
```

### Command Line Method (Batch Processing)

For batch processing, use the `--use-llm` flag:
```
python parse_batch.py --input-dir ./docs --use-llm
```

## Performance Monitoring

The system tracks usage statistics for each parser method:

- Access statistics via the API: `GET /stats`
- View statistics in the logs when running batch processing

## Troubleshooting

If you encounter problems:

1. Check your OpenAI API key is valid and has sufficient quota
2. Look for errors in the logs (check console output)
3. For rate limiting issues, add delays between document processing
4. Verify document formats are supported
5. For large documents, try processing smaller chunks separately 