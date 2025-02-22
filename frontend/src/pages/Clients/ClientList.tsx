// src/pages/Clients/ClientList.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Alert } from '../../components/ui/alert';

interface Client {
  id: string;
  name: string;
  email: string;
  phone: string;
}

const ClientList = () => {
  const { token } = useAuth();
  const [clients, setClients] = useState<Client[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const response = await axios.get('/api/clients', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setClients(response.data);
      } catch (err) {
        setError('Error al cargar los clientes');
      } finally {
        setLoading(false);
      }
    };

    fetchClients();
  }, [token]);

  return (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold mb-4">Lista de Clientes</h2>

      {error && <Alert variant="destructive">{error}</Alert>}

      {loading ? (
        <p>Cargando clientes...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clients.map((client) => (
            <Card key={client.id} className="p-4">
              <h3 className="text-lg font-semibold">{client.name}</h3>
              <p>Email: {client.email}</p>
              <p>Teléfono: {client.phone}</p>
              <Button className="mt-2">Ver Detalles</Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ClientList;
