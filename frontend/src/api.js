const API = "/api";

export async function register(data) {
  const res = await fetch(`${API}/register/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return res.json();
}
export async function logout() {
  const res = await fetch(`${API}/logout/``, {
    method: "POST",
    credentials: "include",
  });
  return res.json();
}