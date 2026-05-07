import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";
import "../Projects/Projects.css";
import "./Dashboard.css";

function Dashboard() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [favorites, setFavorites] = useState([]);
  const [loadingFavorites, setLoadingFavorites] = useState(true);

  useEffect(() => {
    api.get("/my/").then((res) => setUser(res.data));

    api.get("/projects/favorites/")
      .then((res) => setFavorites(res.data))
      .finally(() => setLoadingFavorites(false));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Overview</p>
          <h1 className="page-title">Dashboard</h1>
        </div>

        {user && (
          <p className="welcome-text">
            Witaj, <strong>{user.username}</strong>
          </p>
        )}
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Ulubione projekty</span>
          <span className="stat-value">{favorites.length}</span>
        </div>
      </div>

      <div className="section">
        <h2 className="section-title">Ulubione projekty</h2>

        {loadingFavorites && (
          <div className="state-msg">Ładowanie…</div>
        )}

        {!loadingFavorites && favorites.length === 0 && (
          <div className="empty-state">
            <p>
              Brak ulubionych projektów.{" "}
              <a href="/explore">Odkryj projekty →</a>
            </p>
          </div>
        )}

        {!loadingFavorites && favorites.length > 0 && (
          <div className="projects-grid">
            {favorites.map((project) => (
              <article
                key={project.id}
                className="project-card"
                onClick={() => navigate(`/projects/${project.id}`)}
              >
                <div className="project-card-top">
                  <span className="project-owner-label">
                    @{project.owner}
                  </span>

                  <span className="visibility-label public">
                    ★ Ulubione
                  </span>
                </div>

                <h3 className="project-name">{project.name}</h3>

                <div className="project-tags">
                  {project.tags.length > 0 ? (
                    project.tags.map((tag) => (
                      <span key={tag} className="tag-badge">
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="no-tags">brak tagów</span>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;