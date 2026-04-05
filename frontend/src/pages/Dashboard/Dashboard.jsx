import { useEffect, useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../App";
import "./Dashboard.css";

function Dashboard() {
  const [user, setUser] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState("");

  const navigate = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    api.get("/my/")
      .then((res) => setUser(res.data))
      .catch(() => navigate("/login"));
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await api.post("/logout/");
    } catch (err) {
      // ignore
    }
    logout();
    navigate("/login");
  };
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
    <div className="container">
      <h1>Dashboard</h1>
      {user && <p>Welcome, {user.email}!</p>}
      <button className="button" onClick={handleLogout}>Logout</button>
      <button className="button" onClick={() => navigate("/change-password")}>Zmień hasło</button>
      <button className="button" onClick={() => setShowConfirm(true)}  style={{ backgroundColor: "red", color: "white" }}>Usuń konto</button>

      {showConfirm && (
          <div className="modal-overlay">
            <div className="modal">
              <p>Aby usunąć konto wpisz swoje hasło.</p>
              <p style={{ color: "red"}}> UWAGA: Usunięcia nie da się odwrócić. </p>
              <input
                className="input"
                type="password"
                placeholder="Wprowadź hasło"
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
              />
              {deleteError && <p style={{ color: "red" }}>{deleteError}</p>}
              <div className="modal-buttons">
                <button className="button btn-confirm" onClick={handleDeleteAccount}>Tak, usuń</button>
                <button className="button btn-cancel" onClick={() => {
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

export default Dashboard;