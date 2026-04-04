import { useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../App";

function ChangePassword() {
  const [form, setForm] = useState({
    old_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    try {
      await api.post("/change-password/", form);
      setMessage("Password changed successfully!");
      logout();
      navigate("/login");
    } catch (err) {
      const errData = err.response?.data || {};
      setError(errData.old_password || errData.confirm_password || errData.new_password || "Failed to change password");
    }
  };

  return (
    <div className="container">
      <h1>Change Password</h1>

      {message && <p style={{ color: "green" }}>{message}</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <form className="form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="password"
          name="old_password"
          placeholder="Old Password"
          value={form.old_password}
          onChange={handleChange}
          required
        />
        <input
          className="input"
          type="password"
          name="new_password"
          placeholder="New Password"
          value={form.new_password}
          onChange={handleChange}
          required
        />
        <input
          className="input"
          type="password"
          name="confirm_password"
          placeholder="Confirm New Password"
          value={form.confirm_password}
          onChange={handleChange}
          required
        />

        <button type="submit" className="button">Change Password</button>
      </form>

      <button
        className="button"
        style={{ backgroundColor: "#e74c3c", marginTop: "15px" }}
        onClick={() => navigate("/dashboard")}
      >
        Back to Dashboard
      </button>
    </div>
  );
}

export default ChangePassword;