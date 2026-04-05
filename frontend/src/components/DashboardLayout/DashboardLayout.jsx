import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../App";
import api from "../../api";
import "./DashboardLayout.css";

function DashboardLayout({ children }) {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await api.post("/logout/");
    } catch {
      // ignore
    }
    logout();
    navigate("/login");
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="sidebar-brand">
            <span className="brand-icon">◈</span>
            <span className="brand-name">Dashboard</span>
          </div>
          <nav className="sidebar-nav">
            <NavLink to="/dashboard" end className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <span className="nav-icon">⌂</span>
              <span>Strona główna</span>
            </NavLink>
            <NavLink to="/profile" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <span className="nav-icon">☺</span>
              <span>Profil użytkownika</span>
            </NavLink>
            <NavLink to="/projects" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <span className="nav-icon">❏</span>
              <span>Moje projekty</span>
            </NavLink>
          </nav>
        </div>
        <div className="sidebar-bottom">
          <button className="logout-btn" onClick={handleLogout}>
            <span className="nav-icon">☞</span>
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
