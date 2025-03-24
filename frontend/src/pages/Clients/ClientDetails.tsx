// src/pages/Clients/ClientDetails.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// Importa la instancia de Axios configurada
import axiosInstance from '../../lib/axios';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Alert } from '../../components/ui/alert';
import { Edit, ArrowLeft, User, Building2, Mail, Phone, ClipboardCheck } from 'lucide-react';

interface Client {
  id: number;
  name: string;
  business_name: string;
  tax_id: string;
  client_type: string;
  token: string;
  status: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  contract_number?: string;
  contract_start_date?: string;
  contract_end_date?: string;
  service_level?: string;
  billing_address?: string;
  billing_city?: string;
  billing_state?: string;
  billing_country?: string;
}

const ClientDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [client, setClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchClient();
  }, [id]);

  const fetchClient = async () => {
    try {
      const response = await axiosInstance.get(`/clients/${id}`);
      setClient(response.data);
    } catch (err) {
      setError('Error al cargar los datos del cliente');
      console.error('Error fetching client:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-4">Cargando...</div>;
  if (!client) return <div className="p-4">Cliente no encontrado</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            onClick={() => navigate('/clients')}
            className="flex items-center"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver
          </Button>
          <h1 className="text-3xl font-bold">{client.name}</h1>
          <span className={`px-3 py-1 rounded-full text-sm ${
            client.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {client.status}
          </span>
        </div>
        <Button
          onClick={() => navigate(`/clients/${id}/edit`)}
          className="flex items-center"
        >
          <Edit className="h-4 w-4 mr-2" />
          Editar
        </Button>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          {error}
        </Alert>
      )}

      {/* Información General */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Building2 className="h-5 w-5 mr-2" />
            Información de la Empresa
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Razón Social</p>
              <p className="text-lg">{client.business_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">RUC/DNI</p>
              <p className="text-lg">{client.tax_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Tipo de Cliente</p>
              <p className="text-lg capitalize">{client.client_type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Token</p>
              <p className="text-lg capitalize">{client.token}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <User className="h-5 w-5 mr-2" />
            Información de Contacto
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Nombre de Contacto</p>
              <p className="text-lg">{client.contact_name}</p>
            </div>
            <div className="flex items-center">
              <Mail className="h-4 w-4 mr-2 text-gray-400" />
              <a href={`mailto:${client.contact_email}`} className="text-blue-600 hover:text-blue-800">
                {client.contact_email}
              </a>
            </div>
            <div className="flex items-center">
              <Phone className="h-4 w-4 mr-2 text-gray-400" />
              <a href={`tel:${client.contact_phone}`} className="text-blue-600 hover:text-blue-800">
                {client.contact_phone}
              </a>
            </div>
          </div>
        </Card>
      </div>

      {/* Información del Contrato */}
      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <ClipboardCheck className="h-5 w-5 mr-2" />
          Información del Contrato
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-500">Número de Contrato</p>
            <p className="text-lg">{client.contract_number || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Fecha de Inicio</p>
            <p className="text-lg">{client.contract_start_date || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Fecha de Fin</p>
            <p className="text-lg">{client.contract_end_date || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Nivel de Servicio</p>
            <p className="text-lg">{client.service_level || 'N/A'}</p>
          </div>
        </div>
      </Card>

      {/* Dirección de Facturación */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Dirección de Facturación</h2>
        <p className="text-lg">
          {client.billing_address}
          {client.billing_city && `, ${client.billing_city}`}
          {client.billing_state && `, ${client.billing_state}`}
          {client.billing_country && `, ${client.billing_country}`}
        </p>
      </Card>
    </div>
  );
};

export default ClientDetails;
