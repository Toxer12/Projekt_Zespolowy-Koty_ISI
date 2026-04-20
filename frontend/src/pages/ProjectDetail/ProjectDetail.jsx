import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { appApi } from "../../api";
import "../NewProject/ProjectForm.css";
import "./ProjectDetail.css";
import DocumentUpload from "../DocumentUpload/DocumentUpload";

function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [project, setProject]       = useState(null);
  const [loading, setLoading]       = useState(true);
  const [editing, setEditing]       = useState(false);
  const [saving, setSaving]         = useState(false);
  const [deleting, setDeleting]     = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError]           = useState(null);

  const [name, setName]             = useState("");
  const [visibility, setVisibility] = useState("private");
  const [tags, setTags]             = useState([]);
  const [tagInput, setTagInput]     = useState("");

  const fetchProject = async () => {
    setLoading(true);
    try {
      const res = await appApi.get(`/projects/${id}/`);
      setProject(res.data);
    } catch {
      setError("Nie znaleziono projektu.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProject(); }, [id]);

  const startEdit = () => {
    setName(project.name);
    setVisibility(project.visibility);
    setTags([...project.tags]);
    setTagInput("");
    setError(null);
    setEditing(true);
  };

  const cancelEdit = () => { setEditing(false); setError(null); };

  const addTag = (raw) => {
    const tag = raw.trim().toLowerCase();
    if (tag && !tags.includes(tag)) setTags((prev) => [...prev, tag]);
    setTagInput("");
  };

  const removeTag = (tag) => setTags((prev) => prev.filter((t) => t !== tag));

  const handleTagKeyDown = (e) => {
    if (["Enter", ",", " "].includes(e.key)) {
      e.preventDefault();
      addTag(tagInput);
    }
    if (e.key === "Backspace" && tagInput === "" && tags.length > 0) {
      setTags((prev) => prev.slice(0, -1));
    }
  };

  const handleSave = async () => {
    if (!name.trim()) { setError("Nazwa projektu jest wymagana."); return; }
    setSaving(true);
    setError(null);
    try {
      const res = await appApi.patch(`/projects/${id}/`, { name: name.trim(), visibility, tags });
      setProject(res.data);
      setEditing(false);
    } catch (err) {
      setError(err.response?.data?.name?.[0] || "Nie udało się zapisać zmian.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await appApi.delete(`/projects/${id}/`);
      navigate("/projects");
    } catch {
      setError("Nie udało się usunąć projektu.");
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  const formatDate = (iso) => new Date(iso).toLocaleDateString("pl-PL", {
    day: "2-digit", month: "long", year: "numeric",
  });

  if (loading) return <div className="page"><div className="state-msg">Ładowanie…</div></div>;
  if (error && !project) return <div className="page"><div className="state-msg error">{error}</div></div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">
            <span className="breadcrumb" onClick={() => navigate("/projects")}>Moje projekty</span>
            <span className="breadcrumb-sep"> / </span>
            {project.name}
          </p>
          <h1 className="page-title">{project.name}</h1>
        </div>
        <div className="header-actions">
          {!editing && (
            <>
              <button className="ghost-btn" onClick={startEdit}>Edytuj</button>
              <button className="danger-btn" onClick={() => setConfirmDelete(true)}>Usuń</button>
            </>
          )}
        </div>
      </div>

      {!editing && (
        <div className="detail-card">
            <DocumentUpload projectId={id} />
          <div className="detail-row">
            <span className="detail-label">Widoczność</span>
            <span className={`visibility-pill ${project.visibility}`}>
              {project.visibility === "public" ? "🌐 Publiczny" : "🔒 Prywatny"}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Tagi</span>
            <div className="detail-tags">
              {project.tags.length > 0
                ? project.tags.map((t) => <span key={t} className="tag-badge">{t}</span>)
                : <span className="no-tags">brak tagów</span>}
            </div>
          </div>
          <div className="detail-row">
            <span className="detail-label">Utworzono</span>
            <span className="detail-value">{formatDate(project.created_at)}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Ostatnia zmiana</span>
            <span className="detail-value">{formatDate(project.updated_at)}</span>
          </div>
        </div>
      )}

      {/* Edit mode */}
      {editing && (
        <div className="form-card">
          <div className="form-group">
            <label className="form-label">Nazwa projektu</label>
            <input
              className="form-input"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Widoczność</label>
            <div className="radio-group">
              {[["private", "🔒 Prywatny", "Tylko Ty widzisz ten projekt"],
                ["public",  "🌐 Publiczny", "Widoczny dla wszystkich"]].map(([val, label, desc]) => (
                <label key={val} className={`radio-card ${visibility === val ? "selected" : ""}`}>
                  <input
                    type="radio" name="visibility" value={val}
                    checked={visibility === val}
                    onChange={() => setVisibility(val)}
                  />
                  <div>
                    <span className="radio-label">{label}</span>
                    <span className="radio-desc">{desc}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Tagi</label>
            <div className="tags-input-wrap">
              {tags.map((t) => (
                <span key={t} className="tag-chip">
                  {t}
                  <button className="tag-remove" onClick={() => removeTag(t)}>×</button>
                </span>
              ))}
              <input
                className="tags-input"
                type="text"
                placeholder={tags.length === 0 ? "Dodaj tag…" : ""}
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagKeyDown}
                onBlur={() => tagInput.trim() && addTag(tagInput)}
              />
            </div>
            <p className="form-hint">Oddziel tagi Enterem, spacją lub przecinkiem.</p>
          </div>

          {error && <p className="form-error">{error}</p>}

          <div className="form-actions">
            <button className="ghost-btn" onClick={cancelEdit}>Anuluj</button>
            <button className="create-btn" onClick={handleSave} disabled={saving}>
              {saving ? "Zapisywanie…" : "Zapisz zmiany"}
            </button>
          </div>
        </div>
      )}

      {confirmDelete && (
        <div className="overlay">
          <div className="confirm-dialog">
            <h3 className="confirm-title">Usunąć projekt?</h3>
            <p className="confirm-desc">
              Projekt <strong>{project.name}</strong> zostanie trwale usunięty. Tej operacji nie można cofnąć.
            </p>
            <div className="confirm-actions">
              <button className="ghost-btn" onClick={() => setConfirmDelete(false)}>Anuluj</button>
              <button className="danger-btn" onClick={handleDelete} disabled={deleting}>
                {deleting ? "Usuwanie…" : "Tak, usuń"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProjectDetail;
