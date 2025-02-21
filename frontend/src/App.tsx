// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';

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
import AgentList from './pages/Agents/AgentList';
import AgentDetails from './pages/Agents/AgentDetails';

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
  const { isAuthenticated, user } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (user?.must_change_password) {
    return <Navigate to="/change-password" />;
  }
  
  return <>{children}</>;
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Navbar />
        <Routes>
          {/* Rutas públicas */}
          <Route path="/" element={<Home />} />
          <Route path="/forum" element={<Forum />} />
          <Route path="/login" element={<Login />} />
          
          {/* Rutas de autenticación */}
          <Route path="/change-password" element={<ChangePassword />} />
          
          {/* Rutas protegidas */}
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          
          {/* Rutas de clientes */}
          <Route path="/clients" element={<PrivateRoute><ClientList /></PrivateRoute>} />
          <Route path="/clients/create" element={<PrivateRoute><ClientCreate /></PrivateRoute>} />
          <Route path="/clients/:id/edit" element={<PrivateRoute><ClientEdit /></PrivateRoute>} />
          <Route path="/clients/:id" element={<PrivateRoute><ClientDetails /></PrivateRoute>} />
          
          
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;