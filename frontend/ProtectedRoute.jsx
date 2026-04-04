import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import api from "./api";

export default function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    api.get("me/") // your backend endpoint that returns user info
      .then(() => setAuthenticated(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>; // optional spinner
  if (!authenticated) return <Navigate to="/login" />; // redirect if not logged in

  return children; // render protected content
}