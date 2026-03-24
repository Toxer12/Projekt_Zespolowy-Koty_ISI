// panel admina

import { useNavigate } from "react-router-dom";

function Admin() {
  const navigate = useNavigate();

  return (
    <div className="container">
      <h2>Panel admina</h2>

      <button className="button" onClick={() => navigate("/")}>
        Strona główna
      </button>
    </div>
  );
}

export default Admin;