// src/components/Navbar.tsx
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { 
  Printer, 
  Users, 
  Monitor, 
  Network, 
  HardDrive, 
  Settings,
  LogOut 
} from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="flex items-center">
                <Printer className="h-8 w-8 text-blue-600" />
                <span className="ml-2 text-xl font-bold">PrinterManager</span>
              </Link>
            </div>

            {/* Navigation Links */}
            <div className="hidden md:ml-6 md:flex md:space-x-4">
              <Link to="/printers" className="flex items-center px-3 py-2 text-gray-700 hover:text-blue-600">
                <Monitor className="h-5 w-5 mr-1" />
                <span>Monitoreo</span>
              </Link>
              
              <Link to="/clients" className="flex items-center px-3 py-2 text-gray-700 hover:text-blue-600">
                <Users className="h-5 w-5 mr-1" />
                <span>Clientes</span>
              </Link>

              <Link to="/agents" className="flex items-center px-3 py-2 text-gray-700 hover:text-blue-600">
                <Network className="h-5 w-5 mr-1" />
                <span>Agentes</span>
              </Link>

              <Link to="/drivers" className="flex items-center px-3 py-2 text-gray-700 hover:text-blue-600">
                <HardDrive className="h-5 w-5 mr-1" />
                <span>Drivers</span>
              </Link>

              <Link to="/printer-oids" className="flex items-center px-3 py-2 text-gray-700 hover:text-blue-600">
                <Settings className="h-5 w-5 mr-1" />
                <span>OIDs</span>
              </Link>
            </div>
          </div>

          {/* User Menu */}
          <div className="flex items-center">
            {user ? (
              <div className="flex items-center space-x-4">
                <span className="text-gray-700">{user.username}</span>
                <Button 
                  variant="outline"
                  onClick={handleLogout}
                  className="flex items-center"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Cerrar Sesión
                </Button>
              </div>
            ) : (
              <Button onClick={() => navigate('/login')}>
                Iniciar Sesión
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;