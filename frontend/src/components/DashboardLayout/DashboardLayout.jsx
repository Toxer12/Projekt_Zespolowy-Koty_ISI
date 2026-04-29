import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../App";
import api from "../../api";
import "./DashboardLayout.css";

function DashboardLayout({ children }) {
  const { logout } = useAuth();
  const navigate   = useNavigate();

  const handleLogout = async () => {
    try { await api.post("/logout/"); } catch { /* ignore */ }
    logout();
    navigate("/login");
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="sidebar-brand">
            <span className="brand-icon">◈</span>
            <span className="brand-name">Projekt</span>
          </div>
          <nav className="sidebar-nav">
            <NavLink to="/dashboard" end className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <span className="nav-icon">⊞</span>
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/projects" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <span className="nav-icon">❏</span>
              <span>Moje projekty</span>
            </NavLink>
            <NavLink to="/explore" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <span className="nav-icon">◉</span>
              <span>Odkryj</span>
            </NavLink>
            <NavLink to="/invites" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <span className="nav-icon">✉</span>
              <span>Zaproszenia</span>
            </NavLink>
            <NavLink to="/profile" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <span className="nav-icon">◎</span>
              <span>Profil</span>
            </NavLink>
          </nav>
        </div>
        <div className="sidebar-bottom">
          <button className="logout-btn" onClick={handleLogout}>
            <span className="nav-icon">⇥</span>
            <span>Wyloguj</span>
          </button>
        </div>
      </aside>
      <main className="content">
        {children}
      </main>
    </div>
  );
}

export default DashboardLayout;
