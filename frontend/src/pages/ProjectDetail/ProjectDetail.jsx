import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { appApi } from "../../api";
import "../NewProject/ProjectForm.css";
import "./ProjectDetail.css";
import DocumentUpload from "../DocumentUpload/DocumentUpload";

const ROLE_LABELS = { owner: 'Właściciel', admin: 'Admin', editor: 'Edytor', viewer: 'Widz' };
const ROLE_RANK   = { owner: 3, admin: 2, editor: 1, viewer: 0 };

function MembersPanel({ projectId, myRole }) {
  const [members, setMembers]               = useState([]);
  const [loading, setLoading]               = useState(true);
  const [inviteUsername, setInviteUsername] = useState("");
  const [inviteRole, setInviteRole]         = useState("viewer");
  const [inviteError, setInviteError]       = useState("");
  const [inviteSuccess, setInviteSuccess]   = useState("");
  const [sending, setSending]               = useState(false);

  const canManage   = myRole === 'owner' || myRole === 'admin';
  const inviteRoles = myRole === 'admin' ? ['editor', 'viewer'] : ['admin', 'editor', 'viewer'];

  const fetchMembers = async () => {
    try {
      const res = await appApi.get(`/projects/${projectId}/members/`);
      setMembers(res.data);
    } catch { } finally { setLoading(false); }
  };

  useEffect(() => { fetchMembers(); }, [projectId]);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteUsername.trim()) return;
    setSending(true);
    setInviteError(""); setInviteSuccess("");
    try {
      await appApi.post(`/projects/${projectId}/members/invite/`, { username: inviteUsername.trim(), role: inviteRole });
      setInviteSuccess(`Zaproszenie wysłane do "${inviteUsername}".`);
      setInviteUsername("");
    } catch (err) {
      setInviteError(err.response?.data?.error || "Nie udało się wysłać zaproszenia.");
    } finally { setSending(false); }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      const res = await appApi.patch(`/projects/${projectId}/members/${userId}/`, { role: newRole });
      setMembers((prev) => prev.map((m) => m.user_id === userId ? { ...m, role: res.data.role } : m));
    } catch (err) { alert(err.response?.data?.error || "Błąd."); }
  };

  const handleRemove = async (userId, userName) => {
    if (!window.confirm(`Usunąć użytkownika "${userName}" z projektu?`)) return;
    try {
      await appApi.delete(`/projects/${projectId}/members/${userId}/`);
      setMembers((prev) => prev.filter((m) => m.user_id !== userId));
    } catch (err) { alert(err.response?.data?.error || "Błąd."); }
  };

  return (
    <div className="members-panel">
      <h2 className="members-title">Członkowie projektu</h2>
      {loading && <p className="state-msg">Ładowanie…</p>}
      {!loading && (
        <div className="members-list">
          {members.map((m) => {
            const isOwner      = m.role === 'owner';
            const canActOnThis = !isOwner && ROLE_RANK[myRole] > ROLE_RANK[m.role];
            return (
              <div key={m.user_id} className="member-row">
                <div className="member-info">
                  <span className="member-name">{m.user_name}</span>
                  <span className="member-email">{m.user_email}</span>
                </div>
                {canActOnThis ? (
                  <select className="role-select" value={m.role} onChange={(e) => handleRoleChange(m.user_id, e.target.value)}>
                    {inviteRoles.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
                  </select>
                ) : (
                  <span className={`role-pill role-${m.role}`}>{ROLE_LABELS[m.role]}</span>
                )}
                {canActOnThis
                  ? <button className="member-remove" onClick={() => handleRemove(m.user_id, m.user_name)} title="Usuń z projektu">×</button>
                  : <span className="member-remove-placeholder" />
                }
              </div>
            );
          })}
        </div>
      )}
      {canManage && (
        <form className="invite-form" onSubmit={handleInvite}>
          <h3 className="invite-form-title">Zaproś użytkownika</h3>
          <div className="invite-fields">
            <input className="form-input" type="text" placeholder="Nazwa użytkownika" value={inviteUsername} onChange={(e) => setInviteUsername(e.target.value)} />
            <select className="role-select" value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
              {inviteRoles.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
            </select>
            <button className="create-btn" type="submit" disabled={sending}>{sending ? "…" : "Zaproś"}</button>
          </div>
          {inviteError   && <p className="form-error">{inviteError}</p>}
          {inviteSuccess && <p className="form-success">{inviteSuccess}</p>}
        </form>
      )}
    </div>
  );
}

function ProjectDetail() {
  const { id }   = useParams();
  const navigate = useNavigate();

  const [project, setProject]             = useState(null);
  const [loading, setLoading]             = useState(true);
  const [editing, setEditing]             = useState(false);
  const [saving, setSaving]               = useState(false);
  const [deleting, setDeleting]           = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError]                 = useState(null);
  const [name, setName]                   = useState("");
  const [visibility, setVisibility]       = useState("private");
  const [tags, setTags]                   = useState([]);
  const [tagInput, setTagInput]           = useState("");

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

  const myRole        = project?.my_role ?? null;
  const isOwner       = myRole === 'owner';
  const isMember      = myRole !== null;
  const canEdit       = isOwner;
  const canUpload     = myRole === 'owner' || myRole === 'admin' || myRole === 'editor';
  const isPublicGuest = !isMember && project?.visibility === 'public';

  const startEdit  = () => { setName(project.name); setVisibility(project.visibility); setTags([...project.tags]); setTagInput(""); setError(null); setEditing(true); };
  const cancelEdit = () => { setEditing(false); setError(null); };
  const addTag     = (raw) => { const tag = raw.trim().toLowerCase(); if (tag && !tags.includes(tag)) setTags((prev) => [...prev, tag]); setTagInput(""); };
  const removeTag  = (tag) => setTags((prev) => prev.filter((t) => t !== tag));

  const handleTagKeyDown = (e) => {
    if (["Enter", ",", " "].includes(e.key)) { e.preventDefault(); addTag(tagInput); }
    if (e.key === "Backspace" && tagInput === "" && tags.length > 0) setTags((prev) => prev.slice(0, -1));
  };

  const handleSave = async () => {
    if (!name.trim()) { setError("Nazwa projektu jest wymagana."); return; }
    setSaving(true); setError(null);
    try {
      const res = await appApi.patch(`/projects/${id}/`, { name: name.trim(), visibility, tags });
      setProject(res.data); setEditing(false);
    } catch (err) {
      setError(err.response?.data?.name?.[0] || "Nie udało się zapisać zmian.");
    } finally { setSaving(false); }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await appApi.delete(`/projects/${id}/`); navigate("/projects");
    } catch {
      setError("Nie udało się usunąć projektu."); setDeleting(false); setConfirmDelete(false);
    }
  };

  const handleLeave = async () => {
    if (!window.confirm("Opuścić ten projekt?")) return;
    try {
      await appApi.post(`/projects/${id}/leave/`); navigate("/projects");
    } catch (err) { alert(err.response?.data?.error || "Błąd."); }
  };

  const formatDate = (iso) => new Date(iso).toLocaleDateString("pl-PL", { day: "2-digit", month: "long", year: "numeric" });

  if (loading) return <div className="page"><div className="state-msg">Ładowanie…</div></div>;
  if (error && !project) return <div className="page"><div className="state-msg error">{error}</div></div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">
            {isPublicGuest
              ? <><span className="breadcrumb" onClick={() => navigate("/explore")}>Odkryj</span><span className="breadcrumb-sep"> / </span></>
              : <><span className="breadcrumb" onClick={() => navigate("/projects")}>Moje projekty</span><span className="breadcrumb-sep"> / </span></>
            }
            {project.name}
          </p>
          <h1 className="page-title">{project.name}</h1>
        </div>
        <div className="header-actions">
            <button
  className={`favorite-btn ${project.is_favorited ? "active" : ""}`}
  onClick={async () => {
    try {
      const res = await appApi.post(`/projects/${id}/favorite/`);

      setProject((prev) => ({
        ...prev,
        is_favorited: res.data.is_favorited,
      }));
    } catch {
      alert("Nie udało się zaktualizować ulubionych.");
    }
  }}
>
  {project.is_favorited ? "★ Ulubione" : "☆ Dodaj do ulubionych"}
</button>
          {!editing && canEdit && (
            <><button className="ghost-btn" onClick={startEdit}>Edytuj</button><button className="danger-btn" onClick={() => setConfirmDelete(true)}>Usuń</button></>
          )}
          {isMember && !isOwner && (
            <button className="ghost-btn" onClick={handleLeave}>Opuść projekt</button>
          )}
        </div>
      </div>

      {!editing && (
        <div className="detail-card">
          {canUpload && <DocumentUpload projectId={id} canEdit={canUpload} />}
          {isMember && !canUpload && (
            <div className="doc-section">
              <h2 className="doc-section-title">Dokumenty</h2>
              <p className="doc-empty">Masz rolę Widz — możesz tylko przeglądać dokumenty.</p>
            </div>
          )}
          {isPublicGuest && (
            <div className="doc-section">
              <h2 className="doc-section-title">Dokumenty</h2>
              <p className="doc-empty">Dokumenty są widoczne tylko dla członków projektu.</p>
            </div>
          )}
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
          {isMember && (
            <div className="detail-row">
              <span className="detail-label">Twoja rola</span>
              <span className={`role-pill role-${myRole}`}>{ROLE_LABELS[myRole]}</span>
            </div>
          )}
          <div className="detail-row">
            <span className="detail-label">Właściciel</span>
            <span className="detail-value">{project.owner}</span>
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

      {editing && (
        <div className="form-card">
          <div className="form-group">
            <label className="form-label">Nazwa projektu</label>
            <input className="form-input" type="text" value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSave()} autoFocus />
          </div>
          <div className="form-group">
            <label className="form-label">Widoczność</label>
            <div className="radio-group">
              {[["private", "🔒 Prywatny", "Tylko Ty widzisz ten projekt"], ["public", "🌐 Publiczny", "Widoczny dla wszystkich"]].map(([val, label, desc]) => (
                <label key={val} className={`radio-card ${visibility === val ? "selected" : ""}`}>
                  <input type="radio" name="visibility" value={val} checked={visibility === val} onChange={() => setVisibility(val)} />
                  <div><span className="radio-label">{label}</span><span className="radio-desc">{desc}</span></div>
                </label>
              ))}
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Tagi</label>
            <div className="tags-input-wrap">
              {tags.map((t) => (<span key={t} className="tag-chip">{t}<button className="tag-remove" onClick={() => removeTag(t)}>×</button></span>))}
              <input className="tags-input" type="text" placeholder={tags.length === 0 ? "Dodaj tag…" : ""} value={tagInput} onChange={(e) => setTagInput(e.target.value)} onKeyDown={handleTagKeyDown} onBlur={() => tagInput.trim() && addTag(tagInput)} />
            </div>
            <p className="form-hint">Oddziel tagi Enterem, spacją lub przecinkiem.</p>
          </div>
          {error && <p className="form-error">{error}</p>}
          <div className="form-actions">
            <button className="ghost-btn" onClick={cancelEdit}>Anuluj</button>
            <button className="create-btn" onClick={handleSave} disabled={saving}>{saving ? "Zapisywanie…" : "Zapisz zmiany"}</button>
          </div>
        </div>
      )}

      {isMember && <MembersPanel projectId={id} myRole={myRole} />}

      {confirmDelete && (
        <div className="overlay">
          <div className="confirm-dialog">
            <h3 className="confirm-title">Usunąć projekt?</h3>
            <p className="confirm-desc">Projekt <strong>{project.name}</strong> zostanie trwale usunięty.</p>
            <div className="confirm-actions">
              <button className="ghost-btn" onClick={() => setConfirmDelete(false)}>Anuluj</button>
              <button className="danger-btn" onClick={handleDelete} disabled={deleting}>{deleting ? "Usuwanie…" : "Tak, usuń"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProjectDetail;
