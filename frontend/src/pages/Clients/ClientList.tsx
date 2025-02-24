// src/pages/Clients/ClientList.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Loader2, Plus, Search, RefreshCw } from 'lucide-react';
import clientService, { Client } from '../../services/clientService';
import { useToast } from '@/components/ui/use-toast';

const ClientList = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [filteredClients, setFilteredClients] = useState<Client[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const fetchClients = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setRefreshing(true);
      setError(null);
      
      const data = await clientService.getAllClients();
      setClients(data);
      // Aplicar filtros actuales
      applyFilters(data, searchTerm, statusFilter);
    } catch (err: any) {
      console.error('Error fetching clients:', err);
      setError(err.response?.data?.detail || 'Error al cargar los clientes');
      toast({
        variant: "destructive",
        title: "Error",
        description: "No se pudieron cargar los clientes",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const applyFilters = (clientList: Client[], search: string, status: string) => {
    let filtered = [...clientList];
    
    // Aplicar filtro de búsqueda
    if (search.trim()) {
      const searchLower = search.toLowerCase();
      filtered = filtered.filter(client => 
        client.name.toLowerCase().includes(searchLower) ||
        (client.business_name && client.business_name.toLowerCase().includes(searchLower)) ||
        (client.client_code && client.client_code.toLowerCase().includes(searchLower)) ||
        (client.contact_email && client.contact_email.toLowerCase().includes(searchLower))
      );
    }
    
    // Aplicar filtro de estado
    if (status !== 'all') {
      const isActive = status === 'active';
      filtered = filtered.filter(client => client.is_active === isActive);
    }
    
    setFilteredClients(filtered);
  };

  useEffect(() => {
    let isSubscribed = true;
    
    if (isSubscribed) {
      fetchClients();
    }
    
    return () => {
      isSubscribed = false;
    };
  }, []);
  
  useEffect(() => {
    applyFilters(clients, searchTerm, statusFilter);
  }, [searchTerm, statusFilter, clients]);

  const handleCreateClient = () => {
    navigate('/clients/create');
  };

  const handleViewClient = (id: number) => {
    navigate(`/clients/${id}`);
  };

  const handleRefresh = () => {
    fetchClients(false);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Clientes</h1>
        <Button 
          onClick={handleCreateClient} 
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Nuevo Cliente
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6 flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" />
          {error}
        </div>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>Filtrar y buscar clientes</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative w-full sm:w-2/3">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input
                type="text"
                placeholder="Buscar por nombre, código, email..."
                value={searchTerm}
                onChange={handleSearchChange}
                className="pl-8"
              />
            </div>
            <div className="w-full sm:w-1/3">
              <Select 
                value={statusFilter} 
                onValueChange={handleStatusFilterChange}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Filtrar por estado" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="active">Activos</SelectItem>
                  <SelectItem value="inactive">Inactivos</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Button 
              variant="outline" 
              onClick={handleRefresh} 
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Código</TableHead>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Razón Social</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredClients.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-6 text-gray-500">
                      No se encontraron clientes
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredClients.map((client) => (
                    <TableRow key={client.id}>
                      <TableCell>{client.client_code || '-'}</TableCell>
                      <TableCell className="font-medium">{client.name}</TableCell>
                      <TableCell>{client.business_name || '-'}</TableCell>
                      <TableCell>{client.contact_email || '-'}</TableCell>
                      <TableCell>{client.client_type}</TableCell>
                      <TableCell>
                        <Badge 
                          variant={client.is_active ? "success" : "destructive"}
                        >
                          {client.is_active ? 'Activo' : 'Inactivo'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewClient(client.id)}
                        >
                          Ver
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ClientList;