import { useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../App"

function Login() {
  const [form, setForm] = useState({ username: "", password: "" });
  const navigate = useNavigate();
  const { login } = useAuth();

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
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <input name="username" placeholder="username" value={form.username} onChange={handleChange} required />
        <br /><br />
        <input name="password" type="password" placeholder="Password" value={form.password} onChange={handleChange} required />
        <br /><br />
        <button type="submit">Login</button>
      </form>
      <p>No account? <a href="/register">Register here</a></p>
    </div>
  );
}

export default Login;