// strona po zalogowaniu

import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="container">
      <h2>Panel użytkownika</h2>

      <button className="button" onClick={() => navigate("/")}>
        Strona główna
      </button>

      <button className="button">
        Wyloguj
      </button>
    </div>
  );
}

export default Dashboard;