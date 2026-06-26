import { useMemo, useState } from 'react'
import './App.css'

function App() {
  const API_BASE = useMemo(() => 'http://127.0.0.1:8000', [])

  const [pdfFile, setPdfFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [uploadError, setUploadError] = useState(null)

  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [answer, setAnswer] = useState(null)
  const [askError, setAskError] = useState(null)

  async function handleUpload(e) {
    e.preventDefault()
    setUploadError(null)
    setUploadResult(null)
    setAnswer(null)
    setAskError(null)

    if (!pdfFile) {
      setUploadError('Please choose a PDF first.')
      return
    }

    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', pdfFile)

      const res = await fetch(`${API_BASE}/upload_pdf`, {
        method: 'POST',
        body: form,
      })

      const data = await res.json().catch(() => null)
      if (!res.ok) {
        throw new Error(data?.detail || `Upload failed (HTTP ${res.status})`)
      }

      setUploadResult(data)
    } catch (err) {
      setUploadError(err?.message || String(err))
    } finally {
      setUploading(false)
    }
  }

  async function handleAsk(e) {
    e.preventDefault()
    setAskError(null)
    setAnswer(null)

    if (!question.trim()) {
      setAskError('Please type a question.')
      return
    }

    setAsking(true)
    try {
      const res = await fetch(`${API_BASE}/ask_pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      const data = await res.json().catch(() => null)
      if (!res.ok) {
        throw new Error(data?.detail || `Ask failed (HTTP ${res.status})`)
      }

      setAnswer(data)
    } catch (err) {
      setAskError(err?.message || String(err))
    } finally {
      setAsking(false)
    }
  }

  return (
    <>
      <div className="page">
        <header className="header">
          <div>
            <div className="kicker">PDF Chatbot</div>
            <h1>Ask questions from your PDF</h1>
            <p className="sub">
              Upload a PDF to index it into Chroma, then ask questions that are
              answered using that document.
            </p>
          </div>
          <div className="meta">
            <div className="pill">
              API: <code>{API_BASE}</code>
            </div>
            <a className="pill" href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">
              OpenAPI docs
            </a>
          </div>
        </header>

        <main className="grid">
          <section className="card">
            <h2>1) Upload PDF</h2>
            <form onSubmit={handleUpload} className="stack">
              <label className="field">
                <span className="label">PDF file</span>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                />
              </label>

              <button className="btn" type="submit" disabled={uploading}>
                {uploading ? 'Uploading…' : 'Upload & Index'}
              </button>
            </form>

            {uploadError ? (
              <div className="alert error">{uploadError}</div>
            ) : null}

            {uploadResult ? (
              <div className="alert ok">
                Indexed <strong>{uploadResult.chunks_indexed}</strong> chunks.
              </div>
            ) : null}
          </section>

          <section className="card">
            <h2>2) Ask question</h2>
            <form onSubmit={handleAsk} className="stack">
              <label className="field">
                <span className="label">Question</span>
                <textarea
                  rows={4}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask something from the PDF…"
                />
              </label>

              <button className="btn" type="submit" disabled={asking}>
                {asking ? 'Asking…' : 'Ask PDF'}
              </button>
            </form>

            {askError ? <div className="alert error">{askError}</div> : null}

            {answer ? (
              <div className="answer">
                <div className="answerHeader">
                  <h3>Answer</h3>
                </div>
                <div className="answerBody">{answer.answer}</div>
                {answer.sources?.length ? (
                  <div className="sources">
                    <div className="label">Sources</div>
                    <ul>
                      {answer.sources.map((s, idx) => (
                        <li key={`${s}-${idx}`}>{s || '(unknown source)'}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : null}
          </section>
        </main>

        <footer className="footer">
          Tip: if you restart the backend, you’ll need to upload the PDF again
          (current Chroma storage is in-memory).
        </footer>
      </div>
    </>
  )
}

export default App
