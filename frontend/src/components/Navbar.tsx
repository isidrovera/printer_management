import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Printer, MessageSquare, User } from 'lucide-react';

const Navbar = () => {
  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <Printer className="h-6 w-6 text-blue-600" />
              <span className="font-bold text-xl">PrinterManager</span>
            </Link>
          </div>
          
          <div className="flex space-x-4">
            <Link to="/forum" className="flex items-center space-x-1 text-gray-600 hover:text-blue-600">
              <MessageSquare className="h-5 w-5" />
              <span>Foro</span>
            </Link>
            <Button onClick={() => {}}>
              <User className="h-5 w-5 mr-2" />
              Iniciar Sesión
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;