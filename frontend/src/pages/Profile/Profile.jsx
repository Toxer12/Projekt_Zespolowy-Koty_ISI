import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../App";
import api from "../../api";
import "./Profile.css";

function Profile() {
  const [user, setUser] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/my/").then((res) => setUser(res.data));
  }, []);

  const handleDeleteAccount = async () => {
    try {
      await api.delete("/delete-account/", { data: { password: deletePassword } });
      logout();
      navigate("/login", { replace: true });
    } catch (err) {
      setDeleteError(err.response?.data?.error || "Failed to delete account");
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">Konto</p>
          <h1 className="page-title">Profil</h1>
        </div>
      </div>

      <div className="profile-grid">
        <div className="profile-card">
          <h2 className="card-title">Informacje o koncie</h2>
          {user && (
              <>
                <div className="info-row">
                  <span className="info-label">Nazwa użytkownika</span>
                  <span className="info-value">{user.username}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Email</span>
                  <span className="info-value">{user.email}</span>
                </div>
              </>
            )}
        </div>
        <div className="profile-card">
          <h2 className="card-title">Bezpieczeństwo</h2>
          <div className="card-actions">
            <button className="action-btn" onClick={() => navigate("/change-password")}>
              Zmiana hasła
            </button>
          </div>
        </div>

        <div className="profile-card danger-card">
          <h2 className="card-title danger-title">Usuwanie konta</h2>
          <p className="danger-desc">Usuń konto i wszystkie dane z nim związane.</p>
          <button className="action-btn danger-btn" onClick={() => setShowConfirm(true)}>
            Usuń Konto
          </button>
        </div>
      </div>

      {showConfirm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3 className="modal-title">Usuń konto</h3>
            <p className="modal-desc" style={{ color: "red" }}>UWAGA: Tej akcji nie można cofnąć. Wpisz swoje hasło aby zaakceptować.</p>
            <input
              className="modal-input"
              type="password"
              placeholder="Aktualne hasło"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
            />
            {deleteError && <p className="modal-error">{deleteError}</p>}
            <div className="modal-buttons">
              <button className="action-btn danger-btn" onClick={handleDeleteAccount}>Tak, usuń</button>
              <button className="action-btn" onClick={() => {
                setShowConfirm(false);
                setDeletePassword("");
                setDeleteError("");
              }}>Anuluj</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Profile;
