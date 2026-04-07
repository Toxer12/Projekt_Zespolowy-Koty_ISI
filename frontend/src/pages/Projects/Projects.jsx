import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../../api";
import "./Projects.css";

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
        <span className={`visibility-dot ${project.visibility}`} title={project.visibility === "public" ? "Publiczny" : "Prywatny"} />
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

function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState("");
  const [visibility, setVisibility] = useState("");
  const [error, setError]         = useState(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search)     params.search     = search;
      if (visibility) params.visibility = visibility;
      const res = await api.get("/projects/", { params });
      setProjects(res.data);
    } catch {
      setError("Nie udało się załadować projektów.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(fetchProjects, 300);
    return () => clearTimeout(t);
  }, [search, visibility]);

  return (
    <div className="page">
      {/* Header */}
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Workspace</p>
          <h1 className="page-title">Moje projekty</h1>
        </div>
        <button className="create-btn" onClick={() => navigate("/projects/new")}>
          + Nowy projekt
        </button>
      </div>

      {/* Filters */}
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

      {/* Content */}
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
            <ProjectCard
              key={p.id}
              project={p}
              onClick={() => navigate(`/projects/${p.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default Projects;
