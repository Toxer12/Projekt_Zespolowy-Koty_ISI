import { useEffect, useState } from "react";
import api from "../../api";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../../App";
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
      setMessage("Account created! Check your email to activate.");
    } catch (err) {
      setMessage("Error: " + (err.response?.data?.detail || "Something went wrong"));
    }
  };

  return (
    <div className="container">
      <h1>Rejestracja</h1>
      <form className="form" onSubmit={handleSubmit}>
        <input className="input" name="username" placeholder="Username" onChange={handleChange} required />
        <input className="input" name="email" type="email" placeholder="Email" onChange={handleChange} required />
        <input className="input" name="password" type="password" placeholder="Password" onChange={handleChange} required />
        <button className="button" type="submit">Register</button>
      </form>
      {message && <p>{message}</p>}
      <p>Masz już konto? <a href="/login">Zaloguj się</a></p>
    </div>
  );
}

export default Register;