import axios from "axios";

// 1. Zmieniony baseURL na główny katalog API
const api = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error) => {
  failedQueue.forEach((prom) => error ? prom.reject(error) : prom.resolve());
  failedQueue = [];
};

export const setupInterceptors = (logout) => {
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const original = error.config;

      // 2. Poprawiona ścieżka sprawdzająca refresh względem nowego baseURL
      if (original.url?.includes("/users/refresh/")) {
        logout();
        return Promise.reject(error);
      }

      if (error.response?.status === 401 && !original._retry) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          }).then(() => api(original)).catch((err) => Promise.reject(err));
        }

        original._retry = true;
        isRefreshing = true;

        try {
          // 3. Poprawiona ścieżka wywołania odświeżania tokena
          await api.post("/users/refresh/");
          processQueue(null);
          return api(original);
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

export default api;