// strona po zalogowaniu

import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();
  const handleLogout = async () => {
    try {
      const data = await logout();
      console.log(data);
      navigate("/login");
    } catch (err) {
      console.error("Logout failed:", err);
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
    </div>
  );
}

export default Dashboard;