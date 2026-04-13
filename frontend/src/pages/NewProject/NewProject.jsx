import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { appApi } from "../../api";
import "./ProjectForm.css";

function NewProject() {
  const navigate = useNavigate();
  const [name, setName]             = useState("");
  const [visibility, setVisibility] = useState("private");
  const [tagInput, setTagInput]     = useState("");
  const [tags, setTags]             = useState([]);
  const [error, setError]           = useState(null);
  const [saving, setSaving]         = useState(false);

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

  const handleSubmit = async () => {
    if (!name.trim()) { setError("Nazwa projektu jest wymagana."); return; }
    setSaving(true);
    setError(null);
    try {
      const res = await appApi.post("/projects/", { name: name.trim(), visibility, tags });
      navigate(`/projects/${res.data.id}`);
    } catch (err) {
      const msg = err.response?.data?.name?.[0] || "Nie udało się utworzyć projektu.";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Workspace</p>
          <h1 className="page-title">Nowy projekt</h1>
        </div>
        <button className="ghost-btn" onClick={() => navigate("/projects")}>
          ← Wróć
        </button>
      </div>

      <div className="form-card">
        {/* Nazwa */}
        <div className="form-group">
          <label className="form-label">Nazwa projektu</label>
          <input
            className="form-input"
            type="text"
            placeholder="Np. Aplikacja webowa, API…"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            autoFocus
          />
        </div>

        {/* Widoczność */}
        <div className="form-group">
          <label className="form-label">Widoczność</label>
          <div className="radio-group">
            {[["private", "🔒 Prywatny", "Tylko Ty widzisz ten projekt"],
              ["public",  "🌐 Publiczny", "Widoczny dla wszystkich"]].map(([val, label, desc]) => (
              <label key={val} className={`radio-card ${visibility === val ? "selected" : ""}`}>
                <input
                  type="radio"
                  name="visibility"
                  value={val}
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

        {/* Tagi */}
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
              placeholder={tags.length === 0 ? "Dodaj tag i naciśnij Enter lub przecinek…" : ""}
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
          <button className="ghost-btn" onClick={() => navigate("/projects")}>Anuluj</button>
          <button className="create-btn" onClick={handleSubmit} disabled={saving}>
            {saving ? "Tworzenie…" : "Utwórz projekt"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default NewProject;
