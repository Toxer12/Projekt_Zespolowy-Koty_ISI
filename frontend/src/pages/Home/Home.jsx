import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
    <div className="container">

      <div className="button-group">
        <button className="button" onClick={() => navigate("/login")}>
          Logowanie
        </button>

        <button className="button" onClick={() => navigate("/register")}>
          Rejestracja
        </button>
      </div>
    </div>
  );
}

export default Home;