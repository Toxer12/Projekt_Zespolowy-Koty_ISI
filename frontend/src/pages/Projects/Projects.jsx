import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { appApi } from "../../api";
import "./Projects.css";

const ROLE_LABELS = { owner: 'Właściciel', admin: 'Admin', editor: 'Edytor', viewer: 'Widz' };

function TagBadge({ name }) {
  return <span className="tag-badge">{name}</span>;
}

function ProjectCard({ project, onClick }) {
  const date = new Date(project.created_at).toLocaleDateString("pl-PL", {
    day: "2-digit", month: "short", year: "numeric",
  });
  return (
    <article className="project-card" onClick={onClick}>
      <div className="project-card-top">
        <span className={`visibility-dot ${project.visibility}`} />
        <span className="project-date">{date}</span>
      </div>
      <h3 className="project-name">{project.name}</h3>
      <div className="project-tags">
        {project.tags.length > 0
          ? project.tags.map((t) => <TagBadge key={t} name={t} />)
          : <span className="no-tags">brak tagów</span>}
      </div>
      <div className="project-card-footer">
        <span className={`visibility-label ${project.visibility}`}>
          {project.visibility === "public" ? "Publiczny" : "Prywatny"}
        </span>
        <span className="card-arrow">→</span>
      </div>
    </article>
  );
}

function SharedProjectCard({ project, onClick }) {
  const date = new Date(project.created_at).toLocaleDateString("pl-PL", {
    day: "2-digit", month: "short", year: "numeric",
  });
  return (
    <article className="project-card" onClick={onClick}>
      <div className="project-card-top">
        <span className="project-owner-label">@{project.owner}</span>
        <span className="project-date">{date}</span>
      </div>
      <h3 className="project-name">{project.name}</h3>
      <div className="project-tags">
        {project.tags.length > 0
          ? project.tags.map((t) => <TagBadge key={t} name={t} />)
          : <span className="no-tags">brak tagów</span>}
      </div>
      <div className="project-card-footer">
        <span className="role-label">{ROLE_LABELS[project.my_role] ?? project.my_role}</span>
        <span className="card-arrow">→</span>
      </div>
    </article>
  );
}

function Projects() {
  const navigate                      = useNavigate();
  const [projects, setProjects]       = useState([]);
  const [shared, setShared]           = useState([]);
  const [loading, setLoading]         = useState(true);
  const [sharedLoading, setSharedLoading] = useState(true);
  const [search, setSearch]           = useState("");
  const [visibility, setVisibility]   = useState("");
  const [error, setError]             = useState(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search)     params.search     = search;
      if (visibility) params.visibility = visibility;
      const res = await appApi.get("/projects/", { params });
      setProjects(res.data);
    } catch {
      setError("Nie udało się załadować projektów.");
    } finally {
      setLoading(false);
    }
  };

  const fetchShared = async () => {
    setSharedLoading(true);
    try {
      const res = await appApi.get("/projects/shared/");
      setShared(res.data);
    } catch {
      // ignore
    } finally {
      setSharedLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(fetchProjects, 300);
    return () => clearTimeout(t);
  }, [search, visibility]);

  useEffect(() => { fetchShared(); }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Workspace</p>
          <h1 className="page-title">Moje projekty</h1>
        </div>
        <button className="create-btn" onClick={() => navigate("/projects/new")}>
          + Nowy projekt
        </button>
      </div>

      <div className="projects-toolbar">
        <input
          className="search-input"
          type="text"
          placeholder="Szukaj po nazwie lub tagu…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="filter-tabs">
          {[["", "Wszystkie"], ["private", "Prywatne"], ["public", "Publiczne"]].map(([val, label]) => (
            <button
              key={val}
              className={`filter-tab ${visibility === val ? "active" : ""}`}
              onClick={() => setVisibility(val)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="state-msg">Ładowanie…</div>}
      {error   && <div className="state-msg error">{error}</div>}

      {!loading && !error && projects.length === 0 && (
        <div className="empty-state">
          <p className="empty-icon">❏</p>
          <p className="empty-text">Brak projektów. Stwórz nowy, aby zacząć.</p>
          <button className="create-btn" onClick={() => navigate("/projects/new")}>
            + Nowy projekt
          </button>
        </div>
      )}

      {!loading && !error && projects.length > 0 && (
        <div className="projects-grid">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onClick={() => navigate(`/projects/${p.id}`)} />
          ))}
        </div>
      )}

      {!sharedLoading && shared.length > 0 && (
        <>
          <div className="section-divider">
            <span className="section-divider-label">Projekty innych użytkowników</span>
          </div>
          <div className="projects-grid">
            {shared.map((p) => (
              <SharedProjectCard key={p.id} project={p} onClick={() => navigate(`/projects/${p.id}`)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default Projects;
