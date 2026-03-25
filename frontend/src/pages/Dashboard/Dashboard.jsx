// strona po zalogowaniu

import { useNavigate } from "react-router-dom";
import { logout } from "../../api";
function Dashboard() {
  const navigate = useNavigate();
  const handleLogout = async () => {
  logout();
  navigate("/login");
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