// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import { Loader2 } from 'lucide-react';
import { Toaster } from "@/components/ui/toaster"

// Páginas públicas
import Home from './pages/Home';
import Forum from './pages/Forum/Forum';
import Login from './pages/Auth/Login';

// Páginas de autenticación
import ChangePassword from './pages/Auth/ChangePassword';

// Páginas del dashboard
import Dashboard from './pages/Dashboard';

// Páginas de clientes
import ClientList from './pages/Clients/ClientList';
import ClientCreate from './pages/Clients/ClientCreate';
import ClientEdit from './pages/Clients/ClientEdit';
import ClientDetails from './pages/Clients/ClientDetails';

// Páginas de agentes
import AgentList from './pages/Agent/AgentList';
import AgentDetails from './pages/Agent/AgentDetails';

// Páginas de drivers
import DriverList from './pages/Drivers/DriverList';
import DriverCreate from './pages/Drivers/DriverCreate';
import DriverEdit from './pages/Drivers/DriverEdit';

// Páginas de monitoreo de impresoras
import PrinterMonitor from './pages/Printers/PrinterMonitor';
import PrinterDetails from './pages/Printers/PrinterDetails';
import PrinterReport from './pages/Printers/PrinterReport';

// Páginas de OIDs
import OIDList from './pages/OIDs/OIDList';
import OIDCreate from './pages/OIDs/OIDCreate';
import OIDEdit from './pages/OIDs/OIDEdit';

// Páginas de túneles
import TunnelList from './pages/Tunnels/TunnelList';

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
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  if (user?.must_change_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />;
  }
  
  return <>{children}</>;
};

const AppRoutes = () => {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <Navbar />
      <Routes>
        {/* Rutas públicas */}
        <Route path="/" element={<Home />} />
        <Route path="/forum" element={<Forum />} />
        <Route path="/login" element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
        } />
        
        {/* Rutas de autenticación */}
        <Route path="/change-password" element={
          <PrivateRoute>
            <ChangePassword />
          </PrivateRoute>
        } />
        
        {/* Rutas protegidas */}
        <Route path="/dashboard" element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        } />
        
        {/* Rutas de clientes */}
        <Route path="/clients" element={
          <PrivateRoute>
            <ClientList />
          </PrivateRoute>
        } />
        <Route path="/clients/create" element={
          <PrivateRoute>
            <ClientCreate />
          </PrivateRoute>
        } />
        <Route path="/clients/:id/edit" element={
          <PrivateRoute>
            <ClientEdit />
          </PrivateRoute>
        } />
        <Route path="/clients/:id" element={
          <PrivateRoute>
            <ClientDetails />
          </PrivateRoute>
        } />

       
        {/* Ruta para manejar páginas no encontradas */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
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