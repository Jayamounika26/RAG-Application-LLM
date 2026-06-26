<img width="2045" height="1267" alt="Screenshot 2026-06-25 195643" src="https://github.com/user-attachments/assets/78b05a99-44dc-456e-a0ed-6423b1ed81f6" />

<img width="2150" height="1300" alt="Screenshot 2026-06-25 195921" src="https://github.com/user-attachments/assets/a176cd2c-f484-433e-aae2-7b43e1299f7f" />







# Langchains

A LangChain-powered app with a FastAPI backend and a React frontend for PDF-based Q&A, plus a simple standalone LangChain demo script.

## Prerequisites

- **Python 3.12+**
- **Node.js** (for the frontend)
- **Ollama** installed and running locally
- Pull the required Ollama models:

```powershell
ollama pull qwen2.5
ollama pull nomic-embed-text
```

- A **`.env`** file in the project root with your Tavily API key (required for the `/ask` web-search endpoint):

```
TAVILY_API_KEY=your_key_here
```

## Install Python dependencies

From the project root:

**Using uv (recommended):**

```powershell
uv sync
```

**Or with pip:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Run the backend

```powershell
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Or with uv:

```powershell
uv run uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Once running, open:

- API home: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

### API endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health page |
| `/leela` | GET | Sample GET endpoint |
| `/ask` | POST | Ask a question (uses Tavily web search) |
| `/upload_pdf` | POST | Upload and index a PDF |
| `/ask_pdf` | POST | Ask a question about the uploaded PDF |

## Run the frontend (PDF chat UI)

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173). The UI connects to the backend at `http://127.0.0.1:8000`.

**Workflow:** upload a PDF → ask questions about it via `/ask_pdf`.

## Optional: run the simple LangChain script

`main.py` is a standalone demo (not part of the web app):

```powershell
uv run python main.py
```

It uses Ollama's `qwen2.5` model to explain a topic.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Connection errors from frontend | Ensure the backend is running on port 8000 |
| Ollama errors | Run `ollama serve` and pull the models listed above |
| `/ask` fails | Set `TAVILY_API_KEY` in `.env` |
| PDF upload fails | Ensure `nomic-embed-text` is pulled in Ollama |
| After backend restart | Re-upload the PDF (Chroma storage is in-memory) |
