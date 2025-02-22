// src/pages/Clients/ClientList.tsx
// src/pages/Clients/ClientList.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axiosInstance from '../../lib/axios';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

interface Client {
  id: number;
  name: string;
  business_name?: string;
  tax_id?: string;
  status?: string;
}

const ClientList = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClients = async () => {
      try {
        setLoading(true);
        const response = await axiosInstance.get('/api/v1/clients', {
          headers: {
            'Accept': 'application/json'
          }
        });
        
        console.log('Response:', response);
        
        if (response.data) {
          setClients(Array.isArray(response.data) ? response.data : []);
        }
      } catch (err) {
        console.error('Error loading clients:', err);
        setError('Error al cargar los clientes');
      } finally {
        setLoading(false);
      }
    };

    fetchClients();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-screen">
      <Loader2 className="h-8 w-8 animate-spin" />
    </div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Clientes</h1>
      <div className="grid gap-4">
        {clients.length === 0 ? (
          <p>No hay clientes registrados</p>
        ) : (
          clients.map(client => (
            <Card key={client.id} className="p-4">
              <h2 className="font-bold">{client.name}</h2>
              <p>{client.business_name}</p>
              <p>{client.tax_id}</p>
              <div className="mt-2">
                <Link to={`/clients/${client.id}`}>
                  <Button variant="outline" size="sm">Ver detalles</Button>
                </Link>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default ClientList;