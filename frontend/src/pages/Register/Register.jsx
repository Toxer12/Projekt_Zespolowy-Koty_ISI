import { useEffect, useState } from "react";
import api from "../../api";
import { Navigate, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../App";
import "./Register.css";
function Register() {
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const { checkAuth, isAuthenticated } = useAuth();


  if (isAuthenticated === null) return null;
    if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/register/", form);
      setMessage("Konto stworzone. Sprawdź swój email.");
    } catch (err) {
      setMessage("Error: " + (err.response?.data?.detail || "Something went wrong"));
    }
  };

  return (
    <div className="container">
      <h1>Rejestracja</h1>
      <form className="form" onSubmit={handleSubmit}>
        <input className="input" name="username" placeholder="Nazwa użytkownika" onChange={handleChange} required />
        <input className="input" name="email" type="email" placeholder="Email" onChange={handleChange} required />
        <input className="input" name="password" type="password" placeholder="Hasło" onChange={handleChange} required />
        <button className="button" type="submit">Zarejestruj się</button>
      </form>
      {message && <p>{message}</p>}
      <p>Masz już konto? <Link to="/login" className="register-link"> Zaloguj się</Link></p>
    </div>
  );
}

export default Register;