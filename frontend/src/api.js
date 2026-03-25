const API = import.meta.env.VITE_API_URL;

let token = localStorage.getItem("access_token");

export async function request(path, options = {}) {
  const token = localStorage.getItem("access_token");
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${API}${path}`, { headers, ...options });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Request failed");
  }
  return res.json();
}


export const login = async (data) => {
  const res = await fetch(`${API}/api/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Nieprawidłowa nazwa użytkownika lub hasło");
  }

  const result = await res.json();
  if (!result.access || !result.refresh) {
    throw new Error("Nieprawidłowa odpowiedź serwera");
  }

  localStorage.setItem("access_token", result.access);
  localStorage.setItem("refresh_token", result.refresh);
  token = result.access;
  return result;
};

export const logout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  token = null;
  return Promise.resolve();
};