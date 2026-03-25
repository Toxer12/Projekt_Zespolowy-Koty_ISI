import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../../api";

function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      navigate("/dashboard");
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    try {
      await login({ username, password });
      navigate("/dashboard");
    } catch (err) {
      setError("Nieprawidłowa nazwa użytkownika lub hasło");
    }
  };

  return (
    <div className="container">
      <h2>Logowanie</h2>
      <form className="form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          className="input"
          type="password"
          placeholder="Hasło"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button className="button" type="submit">Zaloguj</button>
        {error && <p style={{ color: "red" }}>{error}</p>}

        <button
          type="button"
          className="button"
          onClick={() => navigate("/register")}
        >
          Rejestracja
        </button>

        <button
          type="button"
          className="button"
          onClick={() => navigate("/reset-password")}
        >
          Zmień hasło
        </button>
      </form>
    </div>
  );
}

export default Login;