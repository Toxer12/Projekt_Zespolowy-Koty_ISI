import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api";

function ResetPasswordConfirm() {
  const navigate = useNavigate();
  const { uidb64, token } = useParams();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (password !== confirmPassword) {
      setError("Hasła nie są takie same");
      return;
    }

    try {
      await api.post(`/users/reset-password/${uidb64}/${token}/`, { password });
      setMessage("Hasło zostało zmienione. Możesz się teraz zalogować.");
      setTimeout(() => navigate("/login"), 3000);
    } catch (err) {
      const data = err.response?.data;
      if (data?.password) {
        setError (Array.isArray(data.password) ? data.password[0] : data.password);
      } else if (data?.error) {
        setError(data.error);
      } else {
      setError("Nie udało się zmienić hasła.");
      }

    }
  };

  return (
    <div className="container">
      <h2>Ustaw nowe hasło</h2>
      <form className="form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="password"
          placeholder="Nowe hasło"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <input
          className="input"
          type="password"
          placeholder="Potwierdź hasło"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
        <button className="button" type="submit">Zmień hasło</button>
        {message && <p style={{ color: "green" }}>{message}</p>}
        {error && <p style={{ color: "red" }}>{error}</p>}
      </form>
    </div>
  );
}

export default ResetPasswordConfirm;