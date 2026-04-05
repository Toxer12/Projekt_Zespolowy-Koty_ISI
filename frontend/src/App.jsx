import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { createContext, useState, useEffect, useContext, useRef, useCallback } from "react";
import api, { setupInterceptors } from "./api";

import Login from "./pages/Login/Login";
import Register from "./pages/Register/Register";
import Dashboard from "./pages/Dashboard/Dashboard";
import ActivationError from "./pages/ActivationError/ActivationError";
import AlreadyActivated from "./pages/AlreadyActivated/AlreadyActivated";
import ProtectedRoute from "./ProtectedRoute";
import ChangePassword from "./pages/ChangePassword/ChangePassword"

const AuthContext = createContext();
export function useAuth() { return useContext(AuthContext); }

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const logoutRef = useRef(null);

  const login = useCallback(() => setIsAuthenticated(true), []);
  const logout = useCallback(() => setIsAuthenticated(false), []);

  // Keep ref current so interceptor always calls the latest logout
  logoutRef.current = logout;

  useEffect(() => {
    setupInterceptors(() => logoutRef.current());
  }, []);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      await api.get("/my/");
      setIsAuthenticated(true);
    } catch {
      setIsAuthenticated(false);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, checkAuth }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/activation-error" element={<ActivationError />} />
          <Route path="/already-activated" element={<AlreadyActivated />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
          path="/change-password"
          element={
            <ProtectedRoute>
              <ChangePassword />
            </ProtectedRoute>
          }
        />

          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;