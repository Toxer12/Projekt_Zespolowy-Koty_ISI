import { useState } from "react";
import { changeName } from "../../api";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../App";

function ChangeName() {
    const [newName, setNewName] = useState("");
    const [password, setPassword] = useState("");

    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const navigate = useNavigate();
    const { logout } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage("");
        setError("");

        try {
            await changeName(newName, password);
            setMessage("Nazwa zmieniona prawidłowo!");
            logout();
            navigate("/login");
        } catch (err) {
            const data = err.response?.data;
            if (data) {
                const messages = Object.entries(data)
                    .map(([field, errors]) =>
                        Array.isArray(errors) ? errors[0] : errors
                    )
                    .join(" | ");
                setError(messages);
            } else {
                setError("Coś poszło nie tak.");
            }
        }
    };

    return (
        <div className="container">
            <h1>Zmiana nazwy</h1>

            {message && <p style={{ color: "green" }}>{message}</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            <form className="form" onSubmit={handleSubmit}>
                
                <input
                    className="input"
                    type="text"
                    placeholder="Nowa nazwa"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    required
                />

                <input
                    className="input"
                    type="password"
                    placeholder="Hasło"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />

                <button type="submit" className="button">
                    Zmień nazwę
                </button>
            </form>

            <button
                className="action-btn"
                style={{ marginTop: "15px" }}
                onClick={() => navigate("/profile")}
            >
                Powrót do profilu
            </button>
        </div>
    );
}

export default ChangeName;