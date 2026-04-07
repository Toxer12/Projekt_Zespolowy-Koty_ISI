import { useEffect, useState } from "react";
import api from "../../api";
import "./Dashboard.css";

function Dashboard() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.get("/users/my/").then((res) => setUser(res.data));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Overview</p>
          <h1 className="page-title">Dashboard</h1>
        </div>
        {user && <p className="welcome-text">Witaj, <strong>{user.username}</strong></p>}
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Projekty</span>
          <span className="stat-value">0</span>
        </div>
      </div>

      <div className="section">
        <h2 className="section-title">Niedawno używane projekty</h2>
        <div className="empty-state">
          <p>Brak projektów. <a href="/projects">Stwórz nowy -></a></p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
