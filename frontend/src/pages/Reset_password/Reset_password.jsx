import { useNavigate } from "react-router-dom";

function ResetPassword() {
  const navigate = useNavigate();

  return (
    <div className="container">
      <h2>Zmiana hasła</h2>

      <form className="form">
        <input className="input" type="email" placeholder="Email" />

        <button className="button" type="submit">
          Wyślij link
        </button>

        <button
          type="button"
          className="button"
          onClick={() => navigate("/login")}
        >
          Powrót do logowania
        </button>
      </form>
    </div>
  );
}

export default ResetPassword;