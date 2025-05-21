# 🛠️ MVP Build Plan – Intelligent Order Document Parser

Each task below is atomic, testable, and focused on one concern. You can assign them sequentially to an engineering LLM or human collaborator, validating functionality after each.

---

## ✅ PHASE 1: Backend Setup & Document Input

### 1. Initialize Flask backend
- **Start:** No backend exists.
- **End:** Basic Flask app in `run.py` that returns "Hello, world!" at `/`.

---

### 2. Set up file upload route (`/upload`)
- **Start:** Flask is running.
- **End:** A `POST /upload` route accepts `.pdf`, `.png`, `.jpg`, `.txt` files and saves them to a temp directory.

---

### 3. Write a helper function to detect file type
- **Start:** File is saved on disk.
- **End:** Python function returns `'pdf'`, `'image'`, or `'txt'` based on file extension.

---

## 🧾 PHASE 2: Text Extraction (OCR & Parsing)

### 4. Extract text from PDFs using `pdfplumber`
- **Start:** Input is a valid `.pdf`.
- **End:** Return full extracted text from all pages as a string.

---

### 5. Extract text from image files using Tesseract OCR
- **Start:** Input is `.png` or `.jpg`.
- **End:** Return transcribed string using `pytesseract.image_to_string()`.

---

### 6. Handle plain text input (e.g. email body)
- **Start:** Input is a `.txt` file.
- **End:** Return string contents without any transformation.

---

### 7. Create unified text extraction pipeline
- **Start:** File is uploaded.
- **End:** Based on file type, use the appropriate method and return raw text.

---

## ✨ PHASE 3: ML-Based NER Inference

### 8. Load pre-trained NER model (e.g., BERT fine-tuned)
- **Start:** `transformers` installed.
- **End:** Function that loads model and tokenizer from `models/ner_bert_model/`.

---

### 9. Preprocess raw text for tokenization
- **Start:** Raw string text.
- **End:** Tokenized input suitable for BERT (`input_ids`, `attention_mask`).

---

### 10. Run NER model inference on tokenized input
- **Start:** Tokenized text + model.
- **End:** Output list of `(token, tag)` pairs (e.g., `("AXL-123", "B-SKU")`).

---

### 11. Postprocess tagged output into structured fields
- **Start:** Tagged tokens (NER output).
- **End:** Dictionary of extracted entities:
```json
{
  "customer": "...",
  "order_id": "...",
  "line_items": [{"sku": "...", "quantity": ..., "price": ...}],
  "shipping_address": "..."
}

## 📦 PHASE 4: Output Structuring & API
### 12. Define structured JSON schema
Start: None.

End: Schema with strict field names, consistent ordering, and types.

### 13. Build /parse route that returns structured JSON
Start: Text + entity parsing is complete.

End: GET /parse returns structured dictionary from last processed document.

### 14. Add endpoint to download result as .json
Start: Structured dictionary exists.

End: GET /download returns it as a downloadable JSON file.

## 🌐 PHASE 5: Optional Frontend
### 15. Scaffold React app with Vite + Tailwind
Start: Empty frontend/.

End: npm run dev renders a homepage with drag-and-drop file zone.

### 16. Build file upload component (Axios to /upload)
Start: Working Flask backend.

End: File is uploaded to backend and confirmed in UI.

### 17. Build parsed output viewer (JSON table)
Start: Response JSON from /parse.

End: Display line items and shipping info in a table with clean formatting.

## 🧪 PHASE 6: Testing & Evaluation
### 18. Add test file and ground truth in data/ground_truth/
Start: One or more sample orders created manually.

End: Saved gold-standard .json file for test case.

### 19. Write test script to compare output vs. ground truth
Start: Parser outputs structured JSON.

End: Script returns accuracy metrics (e.g., entity-level F1 score).

### 20. Add test_parser.py to validate pipeline end-to-end
Start: All modules are written.

End: Unit test that runs full flow and asserts correctness of output fields.