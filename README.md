# Vectorless RAG Studio

A production-style Retrieval-Augmented Generation application that answers questions over uploaded documents without any vector database.

The project uses:

- FastAPI + Python for ingestion, indexing, retrieval, and answer generation
- SQLite for document, page, section, and indexing metadata
- local JSON and pickle artifacts for BM25 and TF-IDF indexes
- Next.js + TypeScript + Tailwind CSS for a polished dashboard UI
- page-aware and section-aware lexical retrieval with grounded citations

The main implementation lives in [`backend/`](/Users/sairammaruri/Desktop/new%20project/rag-no-vector/backend) and [`frontend/`](/Users/sairammaruri/Desktop/new%20project/rag-no-vector/frontend).

## Final Folder Structure

```text
rag-no-vector/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── generation/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── schemas/
│   │   ├── storage/
│   │   ├── utils/
│   │   └── main.py
│   ├── data/
│   │   ├── index/
│   │   ├── sample_docs/
│   │   └── uploads/
│   ├── tests/
│   ├── .env.example
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── public/
│   ├── types/
│   ├── .env.local.example
│   ├── next.config.js
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
└── README.md
```

## Product Highlights

- Upload `PDF`, `TXT`, and `MD` files from the UI
- Parse PDFs page by page and preserve page numbers for citations
- Detect sections from markdown headings and heading-like text
- Build lexical indexes over both page and section retrieval units
- Fuse BM25, TF-IDF, keyword overlap, exact phrase, and title match scoring
- Filter queries by selected documents
- Show evidence, scores, and context sent to the LLM
- Return grounded answers with citations and a strict fallback when evidence is missing
- Persist recent chat history in the browser

## Retrieval Architecture

### Ingestion

- `DocumentParser` extracts page-aware text from PDFs and creates synthetic pages for text-based files.
- `SectionExtractor` detects headings and builds a lightweight hierarchy with parent-child relationships.
- Parsed content is stored in SQLite as documents, pages, and sections.

### Indexing

- `PageIndexer` materializes retrieval units from stored pages and sections.
- `BM25Retriever` stores a classical BM25 index in `backend/data/index/bm25.pkl`.
- `TFIDFRetriever` stores a TF-IDF matrix in `backend/data/index/tfidf.pkl`.
- `manifest.json` records which documents are currently indexed.

### Query Flow

1. Normalize the user question.
2. Retrieve top page and section candidates with BM25 and TF-IDF.
3. Apply title, heading, keyword overlap, and exact-match boosts.
4. Deduplicate overlapping evidence.
5. Assemble grounded context.
6. Send the context to an OpenAI-compatible chat endpoint.
7. Return the answer, citations, evidence list, score breakdowns, and debug context.

No vector store or embedding database is used anywhere in the application.

## Backend API

The FastAPI server exposes:

- `GET /health`
- `POST /upload`
- `POST /index`
- `POST /query`
- `GET /documents`
- `GET /documents/{id}`
- `GET /documents/{id}/sections`
- `GET /documents/{id}/pages`
- `DELETE /documents/{id}`

### Example API Calls

Upload sample documents:

```bash
cd backend
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "files=@data/sample_docs/company_handbook.md" \
  -F "files=@data/sample_docs/product_notes.txt"
```

Build the lexical index:

```bash
cd backend
curl -X POST "http://127.0.0.1:8000/index" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Ask a grounded question:

```bash
cd backend
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How quickly should remote employees acknowledge critical incidents?",
    "top_k": 6,
    "include_debug": true
  }'
```

## Environment Setup

Backend environment:

```bash
cd backend
cp .env.example .env
```

Frontend environment:

```bash
cd frontend
cp .env.local.example .env.local
```

Recommended backend `.env` values:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
LOG_LEVEL=INFO
```

Recommended frontend `.env.local` value:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Run Instructions

### 1. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:3000
```

## Testing

Run the backend unit tests:

```bash
cd backend
python -m pytest
```

The included tests cover:

- section-aware parsing
- synthetic page creation for text files
- hybrid retrieval ranking
- document-level filtering in retrieval

## Notes

- The right-side evidence panel in the frontend includes a debug accordion showing the final context sent to the model.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
