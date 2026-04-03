const API = import.meta.env.VITE_API_URL;
 
async function refreshToken() {
  const res = await fetch(`${API}/api/token/refresh/`, {
    method: "POST",
    credentials: "include",
  });
  return res.ok;
}
 
export async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const res = await fetch(`${API}${path}`, {
    headers,
    credentials: "include",
    ...options,
  });

  if (res.status === 401) {
    window.location.href = "/login";
    return;
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Request failed");
  }

  if (res.status === 204) return null;
  return res.json();
}

export const login = async (data) => {
  await request("/api/login/", {
    method: "POST",
    body: JSON.stringify(data),
  });
};

export const logout = async () => {
  await request("/api/logout/", { method: "POST" });
};