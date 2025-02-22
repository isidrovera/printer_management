// src/pages/Clients/ClientList.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axiosInstance from '../../lib/axios';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Loader2, Plus, Search } from 'lucide-react';

// Enhanced Client interface with optional properties
interface Client {
  id: number;
  name: string;
  business_name?: string;
  tax_id?: string;
  client_type?: string;
  status?: 'active' | 'inactive' | 'pending' | string;
}

const ClientList = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchClients = async () => {
      try {
        // Reset previous error
        setError(null);
        setLoading(true);

        // Fetch clients with comprehensive error handling
        const response = await axiosInstance.get('/api/v1/clients/', {
          headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        
        // Log full response for debugging
        console.log('Full client response:', response);

        // Handle different possible response structures
        const clientData: Client[] = Array.isArray(response.data) 
          ? response.data 
          : response.data?.clients || [];
        
        // Validate client data
        if (!Array.isArray(clientData)) {
          throw new Error('Invalid client data format');
        }

        setClients(clientData);
      } catch (err: any) {
        // Comprehensive error handling
        const errorMessage = err.response?.data?.error 
          || err.message 
          || 'Error al cargar los clientes';
        
        console.error('Error fetching clients:', err);
        setError(errorMessage);
        setClients([]);
      } finally {
        setLoading(false);
      }
    };

    fetchClients();
  }, []);

  // Client filtering with improved null checks
  const filteredClients = clients.filter(client => {
    const searchTermLower = searchTerm.toLowerCase();
    return (
      client.name?.toLowerCase().includes(searchTermLower) ||
      client.business_name?.toLowerCase().includes(searchTermLower) ||
      client.tax_id?.toLowerCase().includes(searchTermLower)
    );
  });

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <Card className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Clientes</h1>
          <Link to="/clients/create">
            <Button className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Nuevo Cliente
            </Button>
          </Link>
        </div>

        {/* Error handling */}
        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Search input */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Buscar clientes..."
              className="pl-10 pr-4 py-2 w-full border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Clients table */}
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Razón Social</TableHead>
                <TableHead>RUC/DNI</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredClients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    {error ? 'No se pudieron cargar los clientes' : 'No se encontraron clientes'}
                  </TableCell>
                </TableRow>
              ) : (
                filteredClients.map((client) => (
                  <TableRow key={client.id}>
                    <TableCell>{client.name || 'N/A'}</TableCell>
                    <TableCell>{client.business_name || '-'}</TableCell>
                    <TableCell>{client.tax_id || '-'}</TableCell>
                    <TableCell>{client.client_type || '-'}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        client.status === 'active' ? 'bg-green-100 text-green-800' :
                        client.status === 'inactive' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {client.status || 'N/A'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Link to={`/clients/${client.id}`}>
                          <Button variant="outline" size="sm">Ver</Button>
                        </Link>
                        <Link to={`/clients/${client.id}/edit`}>
                          <Button variant="outline" size="sm">Editar</Button>
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Card>
    </div>
  );
};

export default ClientList;