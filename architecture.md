# 🧠 Intelligent Order Document Parser – Project Architecture

This project simulates a lightweight version of Endeavor AI’s order processing agents by ingesting order documents (PDFs, scanned images, emails), extracting structured data, and outputting ERP-ready JSON.

---

## 📁 Project Structure

order-parser/
├── backend/
│ ├── app/
│ │ ├── init.py
│ │ ├── routes.py
│ │ ├── parser.py
│ │ ├── ocr.py
│ │ ├── ner_model.py
│ │ └── utils.py
│ ├── data/
│ │ ├── sample_docs/
│ │ └── ground_truth/
│ ├── models/
│ │ └── ner_bert_model/
│ ├── tests/
│ │ └── test_parser.py
│ ├── requirements.txt
│ └── run.py
├── frontend/
│ ├── public/
│ ├── src/
│ │ ├── components/
│ │ ├── pages/
│ │ ├── App.jsx
│ │ └── index.js
│ ├── tailwind.config.js
│ └── vite.config.js
├── README.md
├── .gitignore
└── docs/
├── architecture.md
└── demo_screenshots/

yaml
Copy
Edit

---

## 🔧 Component Responsibilities

### `backend/`

#### `run.py`
- Flask app entry point
- Initializes API and sets up routes

#### `routes.py`
- Defines endpoints:
  - `/upload`: handle file uploads
  - `/parse`: call the parser pipeline

#### `ocr.py`
- Uses `pytesseract` or `pdfplumber` to extract raw text from:
  - Scanned images
  - Native PDFs
- Handles filetype routing (PDF → direct text | JPG → OCR)

#### `parser.py`
- Cleans raw text using regex and `spaCy`
- Applies rules or calls NER model to extract fields
- Outputs structured dictionary of:
  - Customer info
  - Order ID
  - Line items (SKU, quantity, price)
  - Shipping address

#### `ner_model.py`
- Optional: loads BERT model from `transformers`
- Fine-tunes on labeled entity data if ML mode is used

#### `utils.py`
- Helper functions for:
  - JSON export
  - Field confidence estimation
  - Address normalization

#### `data/sample_docs/`
- Holds sample PDFs, PNGs, or `.txt` files

#### `data/ground_truth/`
- Annotated correct outputs for evaluation

#### `models/`
- Trained BERT or rule templates

#### `tests/`
- Unit tests for parser and OCR

---

### `frontend/` (Optional)

#### `App.jsx`
- Main component: drag-and-drop uploader
- Preview of:
  - Raw extracted text
  - Parsed output (JSON table view)

#### `components/`
- File uploader, result viewer, loading spinner

#### `pages/`
- Upload page
- Output preview page

#### API Calls
- POST to `/upload`
- GET from `/parse`

---

## 🔄 How Services Connect

```plaintext
User Upload (Frontend)
   ↓
[React UI]  →  `/upload` (Flask API)
                   ↓
              OCR Engine (`ocr.py`)
                   ↓
         Cleaned Text → `parser.py`
                   ↓
     ↳ Rule-based or ML NER (`ner_model.py`)
                   ↓
      Structured Output (dict/JSON)
                   ↓
               `/parse` → Frontend
                   ↓
     Table + JSON View in React UI
🌐 API Endpoints (Flask)
Route	Method	Purpose
/upload	POST	Accept file, return raw text
/parse	GET	Return extracted order fields (JSON)

🧪 Evaluation (Optional)
Use ground_truth/ + predicted outputs

Evaluate:

Entity Precision, Recall, F1 (via seqeval)

Order completeness (% fields correctly extracted)

🚀 Deployment Suggestions
Part	Platform
Frontend	Vercel
Backend	Render / Railway
Model	Self-hosted or HuggingFace Hub
OCR	Dockerize Tesseract if needed

📌 Notes
You can disable the frontend if needed and demo with Postman or curl.

Start with rule-based parsing, then upgrade to ML-based NER.

Use Label Studio or doccano if you want to label your own training data.