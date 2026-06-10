import { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { appApi } from "../../api";
import "../Projects/Projects.css";

function TagBadge({ name }) {
  return <span className="tag-badge">{name}</span>;
}

function PublicProjectCard({ project, onClick }) {
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
        <span className="visibility-label public">Publiczny</span>
        <span className="card-arrow">→</span>
      </div>
    </article>
  );
}

const PAGE_SIZE = 9;

function Explore() {
  const navigate            = useNavigate();
  const [projects, setProjects] = useState([]);
  const [page, setPage]     = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState(null);
  const sentinelRef         = useRef(null);
  const loadingRef          = useRef(false);

  const loadPage = useCallback(async (pageNum) => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    try {
      const res = await appApi.get("/projects/public/", {
        params: { page: pageNum, page_size: PAGE_SIZE },
      });
      const { results, next } = res.data;
      setProjects((prev) => pageNum === 1 ? results : [...prev, ...results]);
      setHasMore(!!next);
    } catch {
      setError("Nie udało się załadować projektów.");
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, []);

  // Initial load
  useEffect(() => { loadPage(1); }, [loadPage]);

  // Infinite scroll observer
  useEffect(() => {
    if (!sentinelRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingRef.current) {
          setPage((prev) => prev + 1);
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, projects]);

  // Load next page when page increments
  useEffect(() => {
    if (page > 1) loadPage(page);
  }, [page, loadPage]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Odkryj</p>
          <h1 className="page-title">Publiczne projekty</h1>
        </div>
      </div>

      {error && <div className="state-msg error">{error}</div>}

      {!error && projects.length === 0 && !loading && (
        <div className="empty-state">
          <p className="empty-text">Brak publicznych projektów.</p>
        </div>
      )}

      {projects.length > 0 && (
        <div className="projects-grid">
          {projects.map((p) => (
            <PublicProjectCard
              key={p.id}
              project={p}
              onClick={() => navigate(`/projects/${p.id}`)}
            />
          ))}
        </div>
      )}

      {/* Sentinel div — triggers next page load when visible */}
      <div ref={sentinelRef} style={{ height: 1 }} />

      {loading && <div className="state-msg" style={{ marginTop: "1rem" }}>Ładowanie…</div>}
      {!hasMore && projects.length > 0 && (
        <p className="state-msg" style={{ marginTop: "1rem", color: "#bbb" }}>Koniec wyników</p>
      )}
    </div>
  );
}

export default Explore;
