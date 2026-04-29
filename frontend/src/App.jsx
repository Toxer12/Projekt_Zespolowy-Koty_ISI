import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { createContext, useState, useEffect, useContext, useRef, useCallback } from "react";
import api, { setupInterceptors } from "./api";

import Login             from "./pages/Login/Login";
import Register          from "./pages/Register/Register";
import ActivationError   from "./pages/ActivationError/ActivationError";
import AlreadyActivated  from "./pages/AlreadyActivated/AlreadyActivated";
import ResetPassword     from "./pages/ResetPassword/ResetPassword";
import ResetPasswordConfirm from "./pages/ResetPasswordConfirm/ResetPasswordConfirm";
import ChangePassword    from "./pages/ChangePassword/ChangePassword";

import DashboardLayout   from "./components/DashboardLayout/DashboardLayout";
import Dashboard         from "./pages/Dashboard/Dashboard";
import Profile           from "./pages/Profile/Profile";
import Projects          from "./pages/Projects/Projects";
import NewProject        from "./pages/NewProject/NewProject";
import ProjectDetail     from "./pages/ProjectDetail/ProjectDetail";
import Explore           from "./pages/Explore/Explore";
import Invites           from "./pages/Invites/Invites";

import ProtectedRoute    from "./ProtectedRoute";

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const logoutRef = useRef(null);

  const login  = useCallback(() => setIsAuthenticated(true),  []);
  const logout = useCallback(() => setIsAuthenticated(false), []);

  logoutRef.current = logout;

  const checkAuth = async () => {
    try {
      await api.get("/my/");
      setIsAuthenticated(true);
    } catch {
      setIsAuthenticated(false);
    }
  };

  useEffect(() => {
    setupInterceptors(() => logoutRef.current());
  }, []);

  useEffect(() => {
    checkAuth();
  }, []);

  const protect = (Page) => (
    <ProtectedRoute>
      <DashboardLayout><Page /></DashboardLayout>
    </ProtectedRoute>
  );

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, checkAuth, setIsAuthenticated }}>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login"                           element={<Login />} />
          <Route path="/register"                        element={<Register />} />
          <Route path="/activation-error"                element={<ActivationError />} />
          <Route path="/already-activated"               element={<AlreadyActivated />} />
          <Route path="/reset-password"                  element={<ResetPassword />} />
          <Route path="/reset-password/:uidb64/:token"   element={<ResetPasswordConfirm />} />

          {/* Protected */}
          <Route path="/dashboard"       element={protect(Dashboard)} />
          <Route path="/projects"        element={protect(Projects)} />
          <Route path="/projects/new"    element={protect(NewProject)} />
          <Route path="/projects/:id"    element={protect(ProjectDetail)} />
          <Route path="/explore"         element={protect(Explore)} />
          <Route path="/invites"         element={protect(Invites)} />
          <Route path="/profile"         element={protect(Profile)} />
          <Route path="/change-password" element={protect(ChangePassword)} />

          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
