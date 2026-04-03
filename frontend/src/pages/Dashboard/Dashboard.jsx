// strona po zalogowaniu

import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { logout, request } from "../../api";

function Dashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    request("/api/me/").catch(() => navigate("/login"));
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/login");

  };

  const handleDeleteAccount = async () => {
    const confirmed = window.confirm(
      "Czy na pewno chcesz usunąć konto? Tej operacji nie można cofnąć."
    );
    if (!confirmed) return;

    const doubleConfirmed = window.confirm(
      "Ostatnie potwierdzenie — konto zostanie trwale usunięte. Kontynuować?"
    );
    if (!doubleConfirmed) return;

    try {
      await request("/api/delete-account/", { method: "DELETE" });
      await logout();
      navigate("/login");
    } catch (error) {
      alert("Nie udało się usunąć konta: " + error.message);
    }
  };

  return (
    <div className="container">
      <h2>Panel użytkownika</h2>

      <button className="button" onClick={() => navigate("/")}>
        Strona główna
      </button>

      <button className="button" onClick={handleLogout}>
        Wyloguj
      </button>

      <button
        className="button"
        onClick={handleDeleteAccount}
        style={{ backgroundColor: "red", color: "white" }}
      >
        Usuń konto
      </button>
    </div>
  );
}

export default Dashboard;