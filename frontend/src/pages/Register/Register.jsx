import { useNavigate } from "react-router-dom";
import { useState } from "react";

function Register() {
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    const res = await fetch("http://localhost:8000/api/register/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(form),
    });

    const data = await res.json();
    console.log(data);

    if (res.ok) {
      setMessage("Zarejestrowano! Sprawdź email i aktywuj konto.");
      setError("");
    } else {
      setError("Błąd rejestracji. Spróbuj ponownie.");
      setMessage("");
    }
  };

  return (
    <div className="container">
      <h2>Rejestracja</h2>

      <form className="form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="text"
          placeholder="Nazwa użytkownika"
          onChange={(e) => setForm({ ...form, username: e.target.value })}
        />

        <input
          className="input"
          type="email"
          placeholder="Email"
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />

        <input
          className="input"
          type="password"
          placeholder="Hasło"
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />

        <button className="button" type="submit">
          Zarejestruj
        </button>

        {message && <p style={{ color: "green" }}>{message}</p>}
        {error && <p style={{ color: "red" }}>{error}</p>}

        <button
          type="button"
          className="button"
          onClick={() => navigate("/login")}
        >
          Logowanie
        </button>
      </form>
    </div>
  );
}

export default Register;