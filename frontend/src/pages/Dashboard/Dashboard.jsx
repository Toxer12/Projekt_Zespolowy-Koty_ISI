// strona po zalogowaniu

import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

import { logout, request } from "../../api";

function Dashboard() {
  const navigate = useNavigate();
   useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      navigate("/login");
    }
  }, [navigate]);

  const handleLogout = async () => {
    logout();
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
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/delete-account/`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        logout();
        navigate("/login");
      } else {
        alert("Nie udało się usunąć konta.");
      }
    } catch (error) {
      alert("Błąd połączenia z serwerem.");
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