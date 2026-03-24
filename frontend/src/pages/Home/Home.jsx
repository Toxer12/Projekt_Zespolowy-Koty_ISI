import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>

      <button onClick={() => navigate("/login")} style={{ margin: "10px" }}>
        Logowanie
      </button>

      <button onClick={() => navigate("/register")} style={{ margin: "10px" }}>
        Rejestracja
      </button>
    </div>
  );
}

export default Home;