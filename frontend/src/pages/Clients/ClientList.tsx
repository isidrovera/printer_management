import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ClientService, Client } from '../../services/ClientService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { useToast } from "@/components/ui/use-toast";
import { Loader2, Plus, Search, MoreVertical, Edit, Trash, Eye } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const ClientList = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const { toast } = useToast();

  // Cargar clientes
  useEffect(() => {
    const loadClients = async () => {
      try {
        setLoading(true);
        const data = await ClientService.getClients(searchTerm);
        setClients(data);
      } catch (err) {
        toast({
          variant: "destructive",
          title: "Error al cargar los clientes"
        });
      } finally {
        setLoading(false);
      }
    };

    loadClients();
  }, [searchTerm]);

  // Eliminar cliente
  const handleDelete = async () => {
    if (!selectedClient?.id) return;
    try {
      await ClientService.deleteClient(selectedClient.id);
      setClients(clients.filter(c => c.id !== selectedClient.id));
      toast({ title: "Cliente eliminado exitosamente" });
      setDeleteDialogOpen(false);
    } catch (err) {
      toast({ variant: "destructive", title: "Error al eliminar el cliente" });
    }
  };

  if (loading) {
    return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;
  }

  return (
    <div className="container p-6">
      <Card className="p-6">
        {/* Header */}
        <div className="flex justify-between mb-6">
          <h1 className="text-2xl font-bold">Clientes</h1>
          <Link to="/clients/create">
            <Button><Plus className="mr-2" /> Nuevo Cliente</Button>
          </Link>
        </div>

        {/* Buscador */}
        <div className="mb-6">
          <Input
            type="text"
            placeholder="Buscar clientes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>

        {/* Tabla */}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>RUC/DNI</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {clients.map((client) => (
              <TableRow key={client.id}>
                <TableCell>{client.name}</TableCell>
                <TableCell>{client.tax_id || '-'}</TableCell>
                <TableCell>
                  <Badge>{client.status}</Badge>
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm"><MoreVertical /></Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem asChild>
                        <Link to={`/clients/${client.id}`}><Eye className="mr-2" /> Ver</Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link to={`/clients/${client.id}/edit`}><Edit className="mr-2" /> Editar</Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => {
                        setSelectedClient(client);
                        setDeleteDialogOpen(true);
                      }}>
                        <Trash className="mr-2" /> Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Diálogo de confirmación */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogTitle>¿Eliminar cliente?</AlertDialogTitle>
          <AlertDialogDescription>Esta acción no se puede deshacer.</AlertDialogDescription>
          <AlertDialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancelar</Button>
            <Button variant="destructive" onClick={handleDelete}>Eliminar</Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default ClientList;