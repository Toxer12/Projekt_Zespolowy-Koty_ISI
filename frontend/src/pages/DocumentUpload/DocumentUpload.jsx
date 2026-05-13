import { useState, useRef, useCallback, useEffect } from "react";
import { appApi } from "../../api";
import "./DocumentUpload.css";
import ChunkPreview from "../ChunkPreview/ChunkPreview";

const ALLOWED_EXTENSIONS = ["pdf", "txt"];
const MAX_SIZE_MB = 10;
const POLL_INTERVAL = 2000; // ms

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validateFile(file) {
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `Niedozwolony format. Akceptujemy: PDF i TXT.`;
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `Plik za duży (${(file.size / 1024 / 1024).toFixed(1)} MB). Limit: ${MAX_SIZE_MB} MB.`;
  }
  return null;
}

// ── Status badge ──────────────────────────────
function StatusBadge({ status }) {
  const map = {
    pending:    { label: "Oczekuje",       cls: "pending" },
    processing: { label: "Przetwarza…",    cls: "processing" },
    ready:      { label: "Gotowy",         cls: "ready" },
    error:      { label: "Błąd",           cls: "error" },
  };
  const { label, cls } = map[status] ?? { label: status, cls: "" };
  return <span className={`doc-status ${cls}`}>{label}</span>;
}

// ── Single document row ───────────────────────
function DocumentRow({ doc, onDelete, onStatusUpdate, projectId, canEdit }) {
  const pollRef = useRef(null);

  useEffect(() => {
    if (doc.status === "pending" || doc.status === "processing") {
      pollRef.current = setInterval(async () => {
        try {
          const res = await appApi.get(`/documents/${doc.id}/`);
          if (res.data.status !== "pending" && res.data.status !== "processing") {
            clearInterval(pollRef.current);
            onStatusUpdate(res.data);
          }
        } catch {
          clearInterval(pollRef.current);
        }
      }, POLL_INTERVAL);
    }
    return () => clearInterval(pollRef.current);
  }, [doc.id, doc.status]);

  const handleDelete = async () => {
    if (!window.confirm(`Usunąć "${doc.original_name}"?`)) return;
    try {
      await appApi.delete(`/documents/${doc.id}/`);
      onDelete(doc.id);
    } catch {
      alert("Nie udało się usunąć dokumentu.");
    }
  };

  return (
    <div className={`doc-row ${doc.status}`}>
      <span className="doc-icon">{doc.file_type === "pdf" ? "📄" : "📝"}</span>
      <div className="doc-info">
        <span className="doc-name">{doc.original_name}</span>
        <span className="doc-meta">{formatSize(doc.file_size)}</span>
        {doc.status === "error" && doc.error_message && (
          <span className="doc-error">{doc.error_message}</span>
        )}
        <ChunkPreview documentId={doc.id} initialDoc={doc} canEdit={canEdit} />
      </div>
      <StatusBadge status={doc.status} />
      {doc.status === "ready" && doc.file_url && (
        <a
          className="doc-download"
          href={doc.file_url}
          target="_blank"
          rel="noreferrer"
          title="Pobierz"
        >↓</a>
      )}
      <button className="doc-delete" onClick={handleDelete} title="Usuń">×</button>
    </div>
  );
}

// ── Main component ────────────────────────────
export default function DocumentUpload({ projectId, canEdit }) {
  const [docs, setDocs]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadErrors, setUploadErrors] = useState([]); // { name, message }[]
  const inputRef = useRef(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await appApi.get(`/documents/list/?project_id=${projectId}`);
        setDocs(res.data);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [projectId]);

  const uploadFiles = useCallback(async (files) => {
    const errors = [];
    const toUpload = [];

    for (const file of files) {
      const err = validateFile(file);
      if (err) errors.push({ name: file.name, message: err });
      else toUpload.push(file);
    }

    setUploadErrors(errors);
    if (toUpload.length === 0) return;

    setUploading(true);
    const uploaded = [];

    for (const file of toUpload) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("project_id", projectId);
      try {
        const res = await appApi.post("/documents/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        uploaded.push(res.data);
      } catch (err) {
        const msg = err.response?.data?.file?.[0] ?? "Błąd uploadu.";
        errors.push({ name: file.name, message: msg });
      }
    }

    setUploadErrors((prev) => [...prev, ...errors]);
    setDocs((prev) => [...uploaded, ...prev]);
    setUploading(false);
  }, [projectId]);

  // Drag & drop
  const onDragOver  = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = ()  => setDragging(false);
  const onDrop      = (e) => {
    e.preventDefault();
    setDragging(false);
    uploadFiles(Array.from(e.dataTransfer.files));
  };
  const onInputChange = (e) => uploadFiles(Array.from(e.target.files));

  const handleStatusUpdate = (updated) => {
    setDocs((prev) => prev.map((d) => d.id === updated.id ? updated : d));
  };
  const handleDelete = (id) => {
    setDocs((prev) => prev.filter((d) => d.id !== id));
  };

  return (
    <section className="doc-section">
      <h2 className="doc-section-title">Dokumenty</h2>

      <div
        className={`dropzone ${dragging ? "active" : ""} ${uploading ? "busy" : ""}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          multiple
          hidden
          onChange={onInputChange}
        />
        <span className="dropzone-icon">{uploading ? "⟳" : "↑"}</span>
        <span className="dropzone-label">
          {uploading
            ? "Przesyłanie…"
            : "Przeciągnij pliki lub kliknij aby wybrać"}
        </span>
        <span className="dropzone-hint">PDF i TXT · maks. 10 MB</span>
      </div>

      {uploadErrors.length > 0 && (
        <div className="upload-errors">
          {uploadErrors.map((e, i) => (
            <p key={i} className="upload-error">
              <strong>{e.name}</strong>: {e.message}
            </p>
          ))}
          <button className="clear-errors" onClick={() => setUploadErrors([])}>
            Zamknij
          </button>
        </div>
      )}

      {loading && <p className="doc-empty">Ładowanie…</p>}
      {!loading && docs.length === 0 && (
        <p className="doc-empty">Brak dokumentów. Dodaj pierwszy plik.</p>
      )}
      {!loading && docs.length > 0 && (
        <div className="doc-list">
          {docs.map((doc) => (
            <DocumentRow
              key={doc.id}
              doc={doc}
              onDelete={handleDelete}
              onStatusUpdate={handleStatusUpdate}
              projectId={projectId}
              canEdit = {canEdit}
            />
          ))}
        </div>
      )}
    </section>
  );
}
