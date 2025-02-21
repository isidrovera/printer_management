import React, { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { MessageSquare, Image, Paperclip, Search } from 'lucide-react';

const Forum = () => {
  const [searchTerm, setSearchTerm] = useState('');

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header del Foro */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Foro de Soporte</h1>
        <Button>
          Nuevo Tema
        </Button>
      </div>

      {/* Barra de búsqueda */}
      <div className="mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar en el foro..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Lista de Temas */}
      <div className="space-y-4">
        {/* Ejemplo de un tema */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-xl hover:text-blue-600 cursor-pointer">
                  Error en firmware HP LaserJet Pro M404
                </CardTitle>
                <p className="text-sm text-gray-500 mt-1">
                  Iniciado por Juan Pérez · hace 2 horas
                </p>
              </div>
              <div className="flex items-center space-x-4 text-gray-500">
                <span className="flex items-center">
                  <MessageSquare className="h-4 w-4 mr-1" />
                  15
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 line-clamp-2">
              Estoy teniendo problemas al actualizar el firmware de mi impresora HP LaserJet Pro M404. El proceso se interrumpe al 50% y muestra un error...
            </p>
            <div className="flex items-center space-x-2 mt-4">
              <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">HP</span>
              <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">Firmware</span>
              <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">Error</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Forum;