// src/pages/Clients/ClientList.tsx
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert } from '../../components/ui/alert';
import { Users, Plus, Edit, Trash2, Eye } from 'lucide-react';
import axios from 'axios';

interface Client {
  id: number;
  name: string;
  business_name: string;
  client_type: string;
  status: string;
  contact_email: string;
}

const ClientList = () => {
  const navigate = useNavigate();
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get('/api/v1/clients');
      setClients(response.data);
    } catch (err) {
      setError('Error al cargar los clientes');
      console.error('Error fetching clients:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('¿Está seguro de eliminar este cliente?')) return;

    try {
      await axios.delete(`/api/v1/clients/${id}`);
      setClients(clients.filter(client => client.id !== id));
    } catch (err) {
      setError('Error al eliminar el cliente');
      console.error('Error deleting client:', err);
    }
  };

  if (loading) return <div className="p-4">Cargando...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Clientes</h1>
        <Button onClick={() => navigate('/clients/create')} className="flex items-center">
          <Plus className="h-5 w-5 mr-2" />
          Nuevo Cliente
        </Button>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          {error}
        </Alert>
      )}

      <div className="grid gap-6">
        {clients.map(client => (
          <Card key={client.id} className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-blue-600 mr-4" />
                <div>
                  <h2 className="text-xl font-semibold">{client.name}</h2>
                  <p className="text-gray-600">{client.business_name}</p>
                  <p className="text-sm text-gray-500">{client.contact_email}</p>
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  onClick={() => navigate(`/clients/${client.id}`)}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  Ver
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate(`/clients/${client.id}/edit`)}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Editar
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleDelete(client.id)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Eliminar
                </Button>
              </div>
            </div>

            <div className="mt-4 flex space-x-4">
              <span className={`px-2 py-1 rounded-full text-sm ${
                client.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {client.status}
              </span>
              <span className="px-2 py-1 rounded-full bg-blue-100 text-blue-800 text-sm">
                {client.client_type}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ClientList;