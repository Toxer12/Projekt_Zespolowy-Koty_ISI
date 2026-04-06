import { useEffect, useState } from "react";
import api from "../../api";
import { Navigate, useNavigate, Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../../App"
import "./Login.css";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { login, checkAuth, isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const activated = searchParams.get("activated");

  if (isAuthenticated === null) return null;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/login/", form);
      login();
      navigate("/dashboard");
    } catch {
      setError("Nieprawidłowa nazwa użytkownika lub hasło.");
    }
  };

  return (
    <div className="container">
      <h1>Logowanie</h1>
      {activated && <p style={{ color: "green", fontSize: "0.85rem" }}>Konto aktywowane! Możesz się teraz zalogować.</p>}
      <form className="form" onSubmit={handleSubmit}>
        <input className="input" name="email" placeholder="Nazwa użytkownika" value={form.email} onChange={handleChange} required />
        <input className="input" name="password" type="password" placeholder="Hasło" value={form.password} onChange={handleChange} required />
        {error && <p style={{ color: "red", fontSize: "0.85rem" }}>{error}</p>}
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