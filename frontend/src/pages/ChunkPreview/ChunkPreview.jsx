import { useEffect, useState, useRef } from "react";
import { appApi } from "../../api";
import "./ChunkPreview.css";

const EMBEDDING_POLL_INTERVAL = 2500;

function EmbeddingBadge({ status }) {
  const map = {
    none:      { label: "Brak",             cls: "none" },
    chunking:  { label: "Chunking…",        cls: "chunking" },
    embedding: { label: "Embeddingi…",      cls: "embedding" },
    done:      { label: "Embeddingi gotowe", cls: "done" },
    error:     { label: "Błąd",             cls: "error" },
  };
  const { label, cls } = map[status] ?? { label: status, cls: "" };
  return <span className={`emb-badge emb-badge--${cls}`}>{label}</span>;
}

export default function ChunkPreview({ documentId, initialDoc }) {
  const [chunks, setChunks]       = useState([]);
  const [doc, setDoc]             = useState(initialDoc);
  const [loading, setLoading]     = useState(false);
  const [open, setOpen]           = useState(false);
  const [error, setError]         = useState(null);
  const pollRef                   = useRef(null);

  // Polling embedding_status
  useEffect(() => {
    if (!doc) return;
    const active = doc.embedding_status === 'chunking' || doc.embedding_status === 'embedding';
    if (active) {
      pollRef.current = setInterval(async () => {
        try {
          const res = await appApi.get(`/documents/${documentId}/`);
          setDoc(res.data);
          if (res.data.embedding_status !== 'chunking' && res.data.embedding_status !== 'embedding') {
            clearInterval(pollRef.current);
          }
        } catch { clearInterval(pollRef.current); }
      }, EMBEDDING_POLL_INTERVAL);
    }
    return () => clearInterval(pollRef.current);
  }, [doc?.embedding_status]);

  const loadChunks = async () => {
    if (chunks.length > 0) { setOpen(true); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await appApi.get(`/documents/${documentId}/chunks/`);
      setChunks(res.data);
      setOpen(true);
    } catch {
      setError("Nie udało się załadować chunków.");
    } finally {
      setLoading(false);
    }
  };

  if (!doc || doc.status !== 'ready') return null;

  return (
    <div className="chunk-preview">
      <div className="chunk-preview-header">
        <div className="chunk-meta">
          <EmbeddingBadge status={doc.embedding_status} />
          {doc.embedding_status === 'done' && (
            <span className="chunk-count">{doc.chunk_count} chunków</span>
          )}
          {doc.embedding_error && (
            <span className="chunk-error">{doc.embedding_error}</span>
          )}
        </div>

        {doc.embedding_status === 'done' && doc.chunk_count > 0 && (
          <button
            className="chunks-toggle"
            onClick={() => open ? setOpen(false) : loadChunks()}
          >
            {loading ? "Ładowanie…" : open ? "Ukryj chunki ▲" : "Podgląd chunków ▼"}
          </button>
        )}
      </div>

      {error && <p className="chunk-error">{error}</p>}

      {open && chunks.length > 0 && (
        <div className="chunks-list">
          {chunks.map((chunk) => (
            <div key={chunk.id} className="chunk-item">
              <div className="chunk-item-header">
                <span className="chunk-index">#{chunk.index + 1}</span>
                <span className="chunk-chars">{chunk.char_count} zn.</span>
                <span className="chunk-type">{chunk.chunk_type}</span>
              </div>
              <p className="chunk-text">{chunk.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
