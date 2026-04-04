import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../../api";

function Activate() {
  const { uid, token } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    api.get(`activate/${uid}/${token}/`)
      .then(() => {
        alert("Account activated! You are now logged in.");
        navigate("/dashboard");
      })
      .catch(() => {
        alert("Activation failed or link expired.");
        navigate("/login");
      });
  }, [uid, token, navigate]);

  return <div>Activating your account...</div>;
}

export default Activate;