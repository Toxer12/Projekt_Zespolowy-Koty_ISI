import { useNavigate } from "react-router-dom";

function Register() {
  const navigate = useNavigate();
  
  return (
    <div className="container">
      <h2>Rejestracja</h2>

      <form className="form">
        <input className="input" type="text" placeholder="Nazwa użytkownika" />
        <input className="input" type="email" placeholder="Email" />
        <input className="input" type="password" placeholder="Hasło" />
        <button className="button" type="submit">
          Zarejestruj
        </button>

        <button type="button" className="button" onClick={() => navigate("/login")}>
        Logowanie
        </button>
      </form>
    </div>
  );
}

export default Register;