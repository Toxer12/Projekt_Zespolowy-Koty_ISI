import { useEffect, useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../App";

function Dashboard() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const { logout } = useAuth();

  // Initial load of user data
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

  return (
    <div className="container">
      <h1>Dashboard</h1>
      {user && <p>Welcome, {user.email}!</p>}
      <button className="button" onClick={handleLogout}>Logout</button>
      <button className="button" onClick={() => navigate("/change-password")}>Zmień hasło</button>
    </div>
  );
}

export default Dashboard;