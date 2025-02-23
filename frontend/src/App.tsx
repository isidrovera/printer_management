// src/App.tsx
// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import { Loader2 } from 'lucide-react';

// Importaciones de páginas (mantenlas igual)...

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Guardamos la ubicación actual para redireccionar después del login
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  if (user?.must_change_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" state={{ from: location.pathname }} replace />;
  }

  return (
    <>
      <Navbar />
      {children}
    </>
  );
};

const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const from = location.state?.from || '/dashboard';

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
};

const AppRoutes = () => {
  return (
    <Routes>
      {/* Rutas públicas */}
      <Route path="/" element={<Home />} />
      <Route path="/forum" element={<Forum />} />
      <Route 
        path="/login" 
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } 
      />

      {/* Rutas protegidas */}
      <Route 
        path="/change-password" 
        element={
          <PrivateRoute>
            <ChangePassword />
          </PrivateRoute>
        } 
      />

      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />

      {/* Rutas de clientes */}
      <Route path="/clients">
        <Route 
          index 
          element={
            <PrivateRoute>
              <ClientList />
            </PrivateRoute>
          } 
        />
        <Route 
          path="create" 
          element={
            <PrivateRoute>
              <ClientCreate />
            </PrivateRoute>
          } 
        />
        <Route 
          path=":id/edit" 
          element={
            <PrivateRoute>
              <ClientEdit />
            </PrivateRoute>
          } 
        />
        <Route 
          path=":id" 
          element={
            <PrivateRoute>
              <ClientDetails />
            </PrivateRoute>
          } 
        />
      </Route>

      {/* Otras rutas anidadas siguiendo el mismo patrón... */}

      {/* Ruta para manejar páginas no encontradas */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

const App = () => {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
};

export default App;