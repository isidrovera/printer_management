// src/pages/Clients/ClientDetails.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
  CardFooter
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ArrowLeft, 
  Loader2, 
  Edit, 
  Trash2, 
  AlertCircle,
  Building,
  Mail,
  Phone,
  MapPin,
  Calendar,
  UserCog,
  Tag,
  FileText
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose
} from "@/components/ui/dialog";
import clientService, { Client } from '../../services/clientService';
import { useToast } from '@/components/ui/use-toast';

const ClientDetails = () => {
  const { id } = useParams<{ id: string }>();
  const [client, setClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const fetchClient = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await clientService.getClientById(id);
      setClient(data);
    } catch (err: any) {
      console.error('Error fetching client:', err);
      setError(err.response?.data?.detail || 'Error al cargar los datos del cliente');
      toast({
        variant: "destructive",
        title: "Error",
        description: "No se pudieron cargar los datos del cliente",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClient();
  }, [id]);

  const handleEditClient = () => {
    navigate(`/clients/${id}/edit`);
  };

  const handleDeleteClient = async () => {
    if (!id) return;
    
    try {
      setDeleteLoading(true);
      await clientService.deleteClient(id);
      toast({
        title: "Cliente eliminado",
        description: "El cliente ha sido eliminado correctamente",
      });
      navigate('/clients');
    } catch (err: any) {
      console.error('Error deleting client:', err);
      toast({
        variant: "destructive",
        title: "Error",
        description: err.response?.data?.detail || "No se pudo eliminar el cliente",
      });
    } finally {
      setDeleteLoading(false);
      setDeleteDialogOpen(false);
    }
  };

  const handleBack = () => {
    navigate('/clients');
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center mb-6">
          <Button variant="ghost" onClick={handleBack} className="mr-2">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">Detalles del Cliente</h1>
        </div>
        
        <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6 flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" />
          {error || 'No se encontró el cliente'}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center mb-6">
        <Button variant="ghost" onClick={handleBack} className="mr-2">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <h1 className="text-3xl font-bold text-gray-900">Detalles del Cliente</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl">{client.name}</CardTitle>
                  {client.business_name && (
                    <CardDescription className="mt-1">
                      {client.business_name}
                    </CardDescription>
                  )}
                </div>
                <Badge 
                  variant={client.is_active ? "success" : "destructive"}
                  className="ml-2"
                >
                  {client.is_active ? 'Activo' : 'Inactivo'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {client.client_code && (
                  <div className="flex items-start">
                    <Tag className="h-5 w-5 mr-3 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-500">Código de Cliente</p>
                      <p>{client.client_code}</p>
                    </div>
                  </div>
                )}

                {client.contact_email && (
                  <div className="flex items-start">
                    <Mail className="h-5 w-5 mr-3 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-500">Email</p>
                      <p>{client.contact_email}</p>
                    </div>
                  </div>
                )}

                {client.contact_phone && (
                  <div className="flex items-start">
                    <Phone className="h-5 w-5 mr-3 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-500">Teléfono</p>
                      <p>{client.contact_phone}</p>
                    </div>
                  </div>
                )}

                {(client.address || client.city || client.country) && (
                  <div className="flex items-start">
                    <MapPin className="h-5 w-5 mr-3 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-500">Dirección</p>
                      <p>
                        {client.address && `${client.address}, `}
                        {client.city && `${client.city}, `}
                        {client.country && client.country}
                        {client.postal_code && ` (${client.postal_code})`}
                      </p>
                    </div>
                  </div>
                )}

                {client.account_manager && (
                  <div className="flex items-start">
                    <UserCog className="h-5 w-5 mr-3 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-500">Ejecutivo de Cuenta</p>
                      <p>{client.account_manager}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-start">
                  <Building className="h-5 w-5 mr-3 text-gray-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-500">Tipo de Cliente</p>
                    <p>{client.client_type}</p>
                  </div>
                </div>

                {client.service_level && (
                  <div className="flex items-start">
                    <Tag className="h-5 w-5 mr-3 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-500">Nivel de Servicio</p>
                      <p>{client.service_level}</p>
                    </div>
                  </div>
                )}

                {(client.contract_start_date || client.contract_end_date) && (
                  <div className="flex items-start">
                    <Calendar className="h-5 w-5 mr-3 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-500">Contrato</p>
                      <p>
                        {formatDate(client.contract_start_date)} - {formatDate(client.contract_end_date)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex justify-between border-t pt-5">
              <Button 
                variant="outline" 
                onClick={handleEditClient}
                className="flex items-center"
              >
                <Edit className="h-4 w-4 mr-2" />
                Editar
              </Button>
              
              <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="destructive" className="flex items-center">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Eliminar
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>¿Eliminar cliente?</DialogTitle>
                    <DialogDescription>
                      Esta acción no se puede deshacer. ¿Estás seguro que deseas eliminar permanentemente a {client.name}?
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter className="mt-4">
                    <DialogClose asChild>
                      <Button variant="outline">Cancelar</Button>
                    </DialogClose>
                    <Button 
                      variant="destructive" 
                      onClick={handleDeleteClient}
                      disabled={deleteLoading}
                    >
                      {deleteLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      Eliminar
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardFooter>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Tabs defaultValue="details" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="details">Detalles</TabsTrigger>
              <TabsTrigger value="notes">Notas</TabsTrigger>
            </TabsList>
            
            <TabsContent value="details">
              <Card>
                <CardHeader>
                  <CardTitle>Información Adicional</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Información Fiscal</h3>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium text-gray-500">RUT/RFC/NIT</p>
                          <p>{client.tax_id || '-'}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Información del Sistema</h3>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium text-gray-500">Estado del Cliente</p>
                          <p>{client.status}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">ID del Sistema</p>
                          <p>{client.id}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Fecha de Creación</p>
                          <p>{formatDate(client.created_at)}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Última Actualización</p>
                          <p>{formatDate(client.updated_at)}</p>
                        </div>
                        {client.last_contact_date && (
                          <div>
                            <p className="text-sm font-medium text-gray-500">Último Contacto</p>
                            <p>{formatDate(client.last_contact_date)}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="notes">
              <Card>
                <CardHeader>
                  <CardTitle>Notas</CardTitle>
                </CardHeader>
                <CardContent>
                  {client.notes ? (
                    <div className="whitespace-pre-wrap">{client.notes}</div>
                  ) : (
                    <p className="text-gray-500 italic">No hay notas disponibles</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default ClientDetails;