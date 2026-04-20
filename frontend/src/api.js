import axios from "axios";

const BASE = "http://localhost:8000/api";

const DEFAULT_CONFIG = {
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
};

const api = axios.create({
  ...DEFAULT_CONFIG,
  baseURL: `${BASE}/users`,
});

export const appApi = axios.create({
  ...DEFAULT_CONFIG,
  baseURL: BASE,
});

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

      if (original.url?.includes("/refresh/")) {
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