import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api/users",
  withCredentials: true,
});
api.interceptors.request.use((config) => {
  const csrftoken = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="))
    ?.split("=")[1];

  if (csrftoken) {
    config.headers["X-CSRFToken"] = csrftoken;
  }
  return config;
});

export default api;