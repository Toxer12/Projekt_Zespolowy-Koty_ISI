import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();

  return (
    <div className="container">
      <h2>Logowanie</h2>

      <form className="form">
        <input className="input" type="email" placeholder="Email" />
        <input className="input" type="password" placeholder="Hasło" />
        <button className="button" type="submit">
          Zaloguj
        </button>
        <button type="button" className="button" onClick={() => navigate("/register")}>
          Rejestracja
        </button>

        <button type="button" className="button" onClick={() => navigate("/reset-password")}>
          Zmień hasło
        </button>
      </form>
    </div>
  );
}

export default Login;