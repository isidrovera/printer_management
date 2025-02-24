import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ClientService, Client } from '../../services/ClientService';

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
      alert('Error al cargar los clientes');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedClient?.id) return;
    try {
      await ClientService.deleteClient(selectedClient.id);
      setClients(clients.filter(c => c.id !== selectedClient.id));
      alert('Cliente eliminado exitosamente');
      setShowDeleteModal(false);
    } catch (error) {
      alert('Error al eliminar el cliente');
    }
  };

  if (loading) {
    return <div>Cargando...</div>;
  }

  return (
    <div className="p-4">
      <div className="mb-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Clientes</h1>
        <Link to="/clients/create" className="bg-blue-500 text-white px-4 py-2 rounded">
          Nuevo Cliente
        </Link>
      </div>

      <input
        type="text"
        placeholder="Buscar clientes..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-full p-2 border rounded mb-4"
      />

      <div className="overflow-x-auto">
        <table className="w-full border-collapse border">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-2 text-left">Nombre</th>
              <th className="border p-2 text-left">RUC/DNI</th>
              <th className="border p-2 text-left">Estado</th>
              <th className="border p-2 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((client) => (
              <tr key={client.id} className="hover:bg-gray-50">
                <td className="border p-2">{client.name}</td>
                <td className="border p-2">{client.tax_id || '-'}</td>
                <td className="border p-2">
                  <span className={`px-2 py-1 rounded ${
                    client.status === 'active' ? 'bg-green-100 text-green-800' : 
                    client.status === 'inactive' ? 'bg-red-100 text-red-800' : 
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {client.status}
                  </span>
                </td>
                <td className="border p-2 text-right">
                  <div className="flex justify-end gap-2">
                    <Link 
                      to={`/clients/${client.id}`}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Ver
                    </Link>
                    <Link 
                      to={`/clients/${client.id}/edit`}
                      className="text-green-600 hover:text-green-800"
                    >
                      Editar
                    </Link>
                    <button
                      onClick={() => {
                        setSelectedClient(client);
                        setShowDeleteModal(true);
                      }}
                      className="text-red-600 hover:text-red-800"
                    >
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg">
            <h2 className="text-xl mb-4">¿Eliminar cliente?</h2>
            <p className="mb-4">Esta acción no se puede deshacer.</p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 border rounded"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-500 text-white rounded"
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