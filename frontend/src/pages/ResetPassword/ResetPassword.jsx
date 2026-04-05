import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";

function ResetPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    try {
      await api.post("/reset-password/", { email });
      setMessage("Link do zmiany hasła został wysłany na Twój email.");
    } catch (err) {
      setError("Wystąpił błąd. Spróbuj ponownie.");
    }
  };

  return (
    <div className="container">
      <h2>Zmiana hasła</h2>
      <form className="form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <button className="button" type="submit">Wyślij link</button>
        {message && <p style={{ color: "green" }}>{message}</p>}
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="button" className="button" onClick={() => navigate("/login")}>
          Powrót do logowania
        </button>
      </form>
    </div>
  );
}

export default ResetPassword;