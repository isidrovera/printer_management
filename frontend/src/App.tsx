// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import { Loader2 } from 'lucide-react';
import { Toaster } from "@/components/ui/toaster";

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

// Comenta las importaciones que causan problemas
// import DriverList from './pages/Drivers/DriverList';
// import DriverCreate from './pages/Drivers/DriverCreate';
// import DriverEdit from './pages/Drivers/DriverEdit';

// Páginas de monitoreo de impresoras
import PrinterMonitor from './pages/Printers/PrinterList';
import PrinterDetails from './pages/Printers/PrinterForm';

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
  const location = useLocation();
  
  // No mostrar Navbar en la página de dashboard
  const showNavbar = location.pathname !== '/dashboard';

  return (
    <>
      {/* Renderizar Navbar condicionalmente */}
      {showNavbar && <Navbar />}
      
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

        {/* Rutas de agentes */}
        <Route path="/agents" element={
          <PrivateRoute>
            <AgentList />
          </PrivateRoute>
        } />
        
        <Route path="/agents/:id" element={
          <PrivateRoute>
            <AgentDetails />
          </PrivateRoute>
        } />

        {/* Comenta las rutas que causan problemas
        <Route path="/drivers" element={
          <PrivateRoute>
            <DriverList />
          </PrivateRoute>
        } />
        <Route path="/drivers/create" element={
          <PrivateRoute>
            <DriverCreate />
          </PrivateRoute>
        } />
        <Route path="/drivers/:id/edit" element={
          <PrivateRoute>
            <DriverEdit />
          </PrivateRoute>
        } />
        */}

        {/* Rutas de impresoras */}
        <Route path="/printers" element={
          <PrivateRoute>
            <PrinterMonitor />
          </PrivateRoute>
        } />
        <Route path="/printers/:id" element={
          <PrivateRoute>
            <PrinterDetails />
          </PrivateRoute>
        } />

        {/* Rutas de OIDs */}
        <Route path="/printer-oids" element={
          <PrivateRoute>
            <OIDList />
          </PrivateRoute>
        } />
        <Route path="/printer-oids/create" element={
          <PrivateRoute>
            <OIDCreate />
          </PrivateRoute>
        } />
        <Route path="/printer-oids/:id/edit" element={
          <PrivateRoute>
            <OIDEdit />
          </PrivateRoute>
        } />

        {/* Rutas de túneles */}
        <Route path="/tunnels" element={
          <PrivateRoute>
            <TunnelList />
          </PrivateRoute>
        } />
        
        {/* Ruta para manejar páginas no encontradas */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
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