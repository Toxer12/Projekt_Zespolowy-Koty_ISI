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

  return res.json();
}