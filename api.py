import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

load_dotenv()

from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatOllama(model="qwen2.5")

search = TavilySearch()

agent = create_agent(
    model=llm,
    tools=[search]
)

# Global state for PDF-based retriever
embeddings = OllamaEmbeddings(model="nomic-embed-text")
pdf_vectorstore: Chroma | None = None


def _word_count(text: str) -> int:
    return len([w for w in text.strip().split() if w])


def _truncate_to_max_words(text: str, max_words: int) -> str:
    words = [w for w in text.strip().split() if w]
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip()

class Question(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def validate_min_words(cls, v: str) -> str:
        if _word_count(v) < 3:
            raise ValueError("Question must contain at least 3 words.")
        return v


class AnswerResponse(BaseModel):
    answer: str

    @field_validator("answer")
    @classmethod
    def validate_max_words(cls, v: str) -> str:
        if _word_count(v) > 50:
            raise ValueError("Answer must contain a maximum of 50 words.")
        return v


class PdfAnswerResponse(AnswerResponse):
    sources: list[str] = []


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
      <head>
        <title>Langchains API</title>
      </head>
      <body style="font-family: sans-serif; padding: 2rem;">
        <h1>Langchains API is running ✅</h1>
        <p>Try these endpoints:</p>
        <ul>
          <li><code>GET /leela</code></li>
          <li><code>POST /ask</code></li>
          <li><code>POST /upload_pdf</code> then <code>POST /ask_pdf</code></li>
          <li><a href="/docs">OpenAPI docs</a></li>
        </ul>
      </body>
    </html>
    """

@app.get("/leela")
def leela():
    return {"status": "ok", "message": "Hii this is leela fetched with GET request"}


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF, index it into Chroma, and make it available for QA.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        # Save to a temporary path (cross-platform)
        file_bytes = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            temp_path = tmp.name

        # Load and split the PDF
        loader = PyPDFLoader(temp_path)
        print(loader)
        documents = loader.load()
        print(documents)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        splits = splitter.split_documents(documents)

        # Build / replace Chroma vectorstore
        global pdf_vectorstore
        pdf_vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            collection_name="pdf-rag",
        )

        return {"status": "ok", "chunks_indexed": len(splits)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")


@app.post("/ask")
def ask_ai(data: Question) -> AnswerResponse:

    response = agent.invoke(
        {
            "messages": [("user", data.question)]
        }
    )

    answer = _truncate_to_max_words(response["messages"][-1].content, 50)
    return AnswerResponse(answer=answer)


@app.post("/ask_pdf")
def ask_pdf(data: Question) -> PdfAnswerResponse:
    """
    Answer a question based only on the uploaded PDF content.
    """
    if pdf_vectorstore is None:
        raise HTTPException(
            status_code=400,
            detail="No PDF indexed yet. Call /upload_pdf first.",
        )

    # Retrieve relevant chunks
    docs = pdf_vectorstore.similarity_search(data.question, k=4)
    context = "\n\n".join(d.page_content for d in docs)

    prompt = (
        "You are a helpful assistant that answers questions "
        "using ONLY the following PDF content.\n\n"
        f"PDF context:\n{context}\n\n"
        f"Question: {data.question}\n\n"
        "Answer based strictly on the PDF. If the answer is not in the PDF, say you don't know."
    )

    llm_response = llm.invoke(prompt)
    answer_raw = getattr(llm_response, "content", str(llm_response))
    answer = _truncate_to_max_words(answer_raw, 50)

    return PdfAnswerResponse(
        answer=answer,
        sources=[str(d.metadata.get("source", "")) for d in docs],
    )