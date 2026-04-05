import { useEffect, useState } from "react";
import api from "../../api";
import { Navigate, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../App"
import "./Login.css";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const navigate = useNavigate();
  const { login, checkAuth, isAuthenticated } = useAuth();

  if (isAuthenticated === null) return null;
    if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/login/", form);
      login();                    // ← important
      navigate("/dashboard");
    } catch (err) {
      alert(err.response?.data?.error || "Login failed");
    }
  };

  return (
    <div className="container">
      <h1>Logowanie</h1>
      <form className="form" onSubmit={handleSubmit}>
        <input className="input" name="email" placeholder="Nazwa użytkownika" value={form.email} onChange={handleChange} required />
        <br /><br />
        <input className="input" name="password" type="password" placeholder="Hasło" value={form.password} onChange={handleChange} required />
        <br /><br />
        <button className="button" type="submit">Login</button>
      </form>
      <p>Nie masz jeszcze konta?<Link to="/register" className="register-link"> Zarejestruj się</Link></p>
      <br />
      <p>Nie pamiętasz hasła?</p>
      <button className="action-btn" onClick={() => navigate("/reset-password")}>Reset hasła</button>
    </div>
  );
}

export default Login;