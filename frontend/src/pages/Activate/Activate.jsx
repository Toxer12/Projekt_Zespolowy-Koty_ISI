import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { request } from "../../api";

function Activate() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("loading");
  const effectRan = useRef(false);

  useEffect(() => {
    if (effectRan.current) return;
    effectRan.current = true;

    const activateAccount = async () => {
      try {
        await request(`/api/activate/${token}/`, { method: "GET" });
        setStatus("success");
      } catch (err) {
        setStatus("error");
      }
    };
    
    activateAccount();
  }, [token]);

  return (
    <div className="container">
      <h2>Aktywacja konta</h2>
      
      {status === "loading" && (
        <div className="form">
          <p>Trwa aktywacja konta, proszę czekać...</p>
        </div>
      )}

      {status === "success" && (
        <div className="form">
          <p>Konto zostało pomyślnie aktywowane!</p>
          <p>Możesz się teraz zalogować.</p>
          <button className="button" onClick={() => navigate("/login")}>
            Przejdź do logowania
          </button>
        </div>
      )}

      {status === "error" && (
        <div className="form">
          <p>Wystąpił błąd podczas aktywacji konta.</p>
          <p>Link może być nieprawidłowy lub stracił ważność.</p>
          <button className="button" onClick={() => navigate("/")}>
            Powrót do strony głównej
          </button>
        </div>
      )}
    </div>
  );
}

export default Activate;