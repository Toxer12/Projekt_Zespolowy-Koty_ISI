import { useState } from "react";
import api from "../../api";
import { Navigate, useNavigate, Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../../App";
import "./Login.css";

function parseLoginError(err) {
  if (!err.response) {
    // Brak odpowiedzi — problem z siecią lub serwer niedostępny
    return "Nie można połączyć się z serwerem. Sprawdź połączenie.";
  }

  const status = err.response.status;
  const data   = err.response.data;

  if (status === 403)
    return "Konto nie zostało jeszcze aktywowane. Sprawdź skrzynkę email.";

  if (status === 400 || status === 401)
    return "Nieprawidłowy adres email lub hasło.";

  if (status === 403 && data?.detail?.toLowerCase().includes('csrf'))
    return "Błąd bezpieczeństwa (CSRF). Odśwież stronę i spróbuj ponownie.";

  if (status >= 500)
    return "Błąd serwera. Spróbuj ponownie za chwilę.";

  return "Wystąpił nieoczekiwany błąd. Spróbuj ponownie.";
}

function AuthLoader() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '100vh', background: '#fafaf8',
    }}>
      <div style={{
        width: 32, height: 32, border: '3px solid #e0e0e0',
        borderTopColor: '#333', borderRadius: '50%',
        animation: 'spin 0.7s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function Login() {
  const [form, setForm]     = useState({ email: "", password: "" });
  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);
  const navigate              = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [searchParams]        = useSearchParams();
  const activated             = searchParams.get("activated");

  if (isAuthenticated === null) return <AuthLoader />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/login/", form);
      login();
      navigate("/dashboard");
    } catch (err) {
      setError(parseLoginError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Logowanie</h1>
      {activated && (
        <p style={{ color: "green", fontSize: "0.85rem" }}>
          Konto aktywowane! Możesz się teraz zalogować.
        </p>
      )}
      <form className="form" onSubmit={handleSubmit}>
        <input
          className="input"
          name="email"
          placeholder="Adres e-mail"
          value={form.email}
          onChange={handleChange}
          required
        />
        <input
          className="input"
          name="password"
          type="password"
          placeholder="Hasło"
          value={form.password}
          onChange={handleChange}
          required
        />
        {error && <p style={{ color: "red", fontSize: "0.85rem" }}>{error}</p>}
        <button className="button" type="submit" disabled={loading}>
          {loading ? "Logowanie…" : "Zaloguj się"}
        </button>
      </form>
      <p>Nie masz jeszcze konta?
        <Link to="/register" className="register-link"> Zarejestruj się</Link>
      </p>
      <br />
      <p>Nie pamiętasz hasła?</p>
      <button className="action-btn" onClick={() => navigate("/reset-password")}>
        Reset hasła
      </button>
    </div>
  );
}

export default Login;
