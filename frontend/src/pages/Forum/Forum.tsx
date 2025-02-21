import React, { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { MessageSquare, Search } from 'lucide-react';
import NewTopicModal from '../../components/Forum/NewTopicModal';

const Forum = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isNewTopicModalOpen, setIsNewTopicModalOpen] = useState(false);

  // Datos de ejemplo para los temas del foro
  const forumTopics = [
    {
      id: 1,
      title: 'Error en firmware HP LaserJet Pro M404',
      author: 'Juan Pérez',
      timeAgo: '2 horas',
      replies: 15,
      content: 'Estoy teniendo problemas al actualizar el firmware de mi impresora HP LaserJet Pro M404. El proceso se interrumpe al 50% y muestra un error...',
      tags: ['HP', 'Firmware', 'Error']
    },
    {
      id: 2,
      title: 'Problema con bandeja de papel Epson L3150',
      author: 'María García',
      timeAgo: '5 horas',
      replies: 8,
      content: 'La bandeja de papel de mi Epson L3150 no está alimentando correctamente. A veces toma varias hojas a la vez y otras veces no toma ninguna...',
      tags: ['Epson', 'Hardware', 'Papel']
    },
    {
      id: 3,
      title: 'Canon Pixma no reconoce cartuchos nuevos',
      author: 'Carlos Rodríguez',
      timeAgo: '1 día',
      replies: 23,
      content: 'Acabo de instalar cartuchos nuevos en mi Canon Pixma pero la impresora no los reconoce. He intentado limpiar los contactos pero sigue sin funcionar...',
      tags: ['Canon', 'Cartuchos', 'Configuración']
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header del Foro */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Foro de Soporte</h1>
        <Button onClick={() => setIsNewTopicModalOpen(true)}>
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
        {forumTopics.map(topic => (
          <Card key={topic.id} className="hover:shadow-lg transition-shadow duration-200">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl hover:text-blue-600 cursor-pointer">
                    {topic.title}
                  </CardTitle>
                  <p className="text-sm text-gray-500 mt-1">
                    Iniciado por {topic.author} · hace {topic.timeAgo}
                  </p>
                </div>
                <div className="flex items-center space-x-4 text-gray-500">
                  <span className="flex items-center">
                    <MessageSquare className="h-4 w-4 mr-1" />
                    {topic.replies}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 line-clamp-2">
                {topic.content}
              </p>
              <div className="flex items-center space-x-2 mt-4">
                {topic.tags.map((tag, index) => (
                  <span 
                    key={index} 
                    className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Modal de Nuevo Tema */}
      <NewTopicModal 
        isOpen={isNewTopicModalOpen}
        onClose={() => setIsNewTopicModalOpen(false)}
      />
    </div>
  );
};

export default Forum;