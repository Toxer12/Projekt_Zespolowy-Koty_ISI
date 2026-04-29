import { useEffect, useState } from "react";
import { appApi } from "../../api";
import "../Projects/Projects.css";

function TagBadge({ name }) {
  return <span className="tag-badge">{name}</span>;
}

function PublicProjectCard({ project }) {
  const date = new Date(project.created_at).toLocaleDateString("pl-PL", {
    day: "2-digit", month: "short", year: "numeric",
  });

  return (
    <article className="project-card">
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
        <span className="visibility-label public">Publiczny</span>
      </div>
    </article>
  );
}

function Explore() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  useEffect(() => {
    appApi.get("/projects/public/")
      .then((res) => setProjects(res.data))
      .catch(() => setError("Nie udało się załadować projektów."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Odkryj</p>
          <h1 className="page-title">Publiczne projekty</h1>
        </div>
      </div>

      {loading && <div className="state-msg">Ładowanie…</div>}
      {error   && <div className="state-msg error">{error}</div>}

      {!loading && !error && projects.length === 0 && (
        <div className="empty-state">
          <p className="empty-text">Brak publicznych projektów.</p>
        </div>
      )}

      {!loading && !error && projects.length > 0 && (
        <div className="projects-grid">
          {projects.map((p) => (
            <PublicProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}
    </div>
  );
}

export default Explore;
