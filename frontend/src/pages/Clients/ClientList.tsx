import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ClientService, Client } from '../../services/ClientService';
import { Eye, Edit, Trash2, Plus, Search, X } from 'lucide-react';

const ClientList = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    loadClients();
  }, [searchTerm]);

  const loadClients = async () => {
    try {
      setLoading(true);
      const data = await ClientService.getClients(searchTerm);
      setClients(data);
    } catch (error) {
      // Toast notification would be better here
      console.error('Error al cargar los clientes', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedClient?.id) return;
    try {
      await ClientService.deleteClient(selectedClient.id);
      setClients(clients.filter(c => c.id !== selectedClient.id));
      // Toast notification would be better here
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Error al eliminar el cliente', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-pulse text-gray-400">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-light text-gray-800">Clientes</h1>
        <Link 
          to="/clients/create" 
          className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-full transition-colors shadow-sm flex items-center"
          title="Nuevo Cliente"
        >
          <Plus size={20} />
        </Link>
      </div>

      <div className="relative mb-6">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={18} className="text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Buscar clientes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 p-3 border-0 border-b focus:ring-0 focus:border-blue-500 transition-colors bg-gray-50 rounded-lg"
        />
        {searchTerm && (
          <button 
            onClick={() => setSearchTerm('')}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <X size={18} className="text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">RUC/DNI</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-4 text-right font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {clients.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  No se encontraron clientes
                </td>
              </tr>
            ) : (
              clients.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">{client.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{client.tax_id || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      client.status === 'active' ? 'bg-green-100 text-green-800' : 
                      client.status === 'inactive' ? 'bg-red-100 text-red-800' : 
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {client.status === 'active' ? 'Activo' : 
                       client.status === 'inactive' ? 'Inactivo' : client.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex justify-end gap-2">
                      <Link 
                        to={`/clients/${client.id}`}
                        className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                        title="Ver detalles"
                      >
                        <Eye size={18} />
                      </Link>
                      <Link 
                        to={`/clients/${client.id}/edit`}
                        className="p-1 text-gray-400 hover:text-green-500 transition-colors"
                        title="Editar cliente"
                      >
                        <Edit size={18} />
                      </Link>
                      <button
                        onClick={() => {
                          setSelectedClient(client);
                          setShowDeleteModal(true);
                        }}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        title="Eliminar cliente"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de eliminación */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h2 className="text-xl font-medium mb-3">¿Eliminar cliente?</h2>
            <p className="mb-4 text-gray-600">
              ¿Estás seguro de eliminar a <span className="font-medium">{selectedClient?.name}</span>? Esta acción no se puede deshacer.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md transition-colors"
              >
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientList;