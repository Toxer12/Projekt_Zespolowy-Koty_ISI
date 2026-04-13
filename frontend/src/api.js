import axios from "axios";

const BASE = "http://localhost:8000/api";

const DEFAULT_CONFIG = {
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
};

// Instance dla użytkowników (auth, login, register, itd.)
const api = axios.create({
  ...DEFAULT_CONFIG,
  baseURL: `${BASE}/users`,
});

// Instance dla projektów i dokumentów
export const appApi = axios.create({
  ...DEFAULT_CONFIG,
  baseURL: BASE,
});

// ── Wspólna logika refresh ─────────────────────────────────────────────────
let isRefreshing = false;
let failedQueue  = [];

const processQueue = (error) => {
  failedQueue.forEach((prom) => error ? prom.reject(error) : prom.resolve());
  failedQueue = [];
};

const createInterceptor = (instance, logout) => {
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const original = error.config;

      // Jeśli to sam /refresh/ się wyłożył — wyloguj
      if (original.url?.includes("/users/refresh/")) {
        logout();
        return Promise.reject(error);
      }

      if (error.response?.status === 401 && !original._retry) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then(() => instance(original))
            .catch((err) => Promise.reject(err));
        }

        original._retry  = true;
        isRefreshing     = true;

        try {
          // Refresh zawsze przez główne api (users instance)
          await api.post("/refresh/");
          processQueue(null);
          return instance(original);
        } catch (refreshError) {
          processQueue(refreshError);
          logout();
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      return Promise.reject(error);
    }
  );
};

export const setupInterceptors = (logout) => {
  createInterceptor(api,    logout);
  createInterceptor(appApi, logout);
};

export default api;