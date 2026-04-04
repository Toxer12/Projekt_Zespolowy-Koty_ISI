import { useEffect, useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../App";

function Dashboard() {
  const [user, setUser] = useState(null);
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
    logout();           // ← important: this clears React state
    navigate("/login");
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>Dashboard</h1>
      {user && <p>Welcome, {user.email}!</p>}
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}

export default Dashboard;