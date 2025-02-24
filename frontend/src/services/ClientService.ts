// src/services/clientService.ts
import axiosInstance from '../lib/axios';

export interface Client {
  id: number;
  name: string;
  business_name?: string;
  tax_id?: string;
  client_code?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  city?: string;
  country?: string;
  postal_code?: string;
  account_manager?: string;
  service_level?: string;
  client_type: string;
  status: string;
  is_active: boolean;
  notes?: string;
  contract_start_date?: string;
  contract_end_date?: string;
  last_contact_date?: string;
  token?: string;
  created_at: string;
  updated_at: string;
}

export interface ClientCreate {
  name: string;
  business_name?: string;
  tax_id?: string;
  client_code?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  city?: string;
  country?: string;
  postal_code?: string;
  account_manager?: string;
  service_level?: string;
  client_type: string;
  status: string;
  is_active: boolean;
  notes?: string;
  contract_start_date?: string;
  contract_end_date?: string;
}

export interface ClientUpdate extends Partial<ClientCreate> {}

export interface ClientDashboardStats {
  total: number;
  active: number;
  inactive: number;
  by_type: Record<string, number>;
  active_contracts: number;
  last_updated: string;
}

const ClientService = {
  // Obtener todos los clientes
  getAllClients: async (): Promise<Client[]> => {
    try {
      const response = await axiosInstance.get('/clients');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Obtener un cliente por ID
  getClientById: async (id: number | string): Promise<Client> => {
    try {
      const response = await axiosInstance.get(`/clients/${id}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Crear un nuevo cliente
  createClient: async (clientData: ClientCreate): Promise<Client> => {
    try {
      const response = await axiosInstance.post('/clients', clientData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Actualizar un cliente existente
  updateClient: async (id: number | string, clientData: ClientUpdate): Promise<Client> => {
    try {
      const response = await axiosInstance.put(`/clients/${id}`, clientData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Eliminar un cliente
  deleteClient: async (id: number | string): Promise<{ message: string }> => {
    try {
      const response = await axiosInstance.delete(`/clients/${id}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Buscar clientes
  searchClients: async (searchTerm: string): Promise<Client[]> => {
    try {
      const response = await axiosInstance.get(`/clients/search/${searchTerm}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Obtener clientes por estado
  getClientsByStatus: async (status: string): Promise<Client[]> => {
    try {
      const response = await axiosInstance.get(`/clients/status/${status}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Obtener clientes por nivel de servicio
  getClientsByServiceLevel: async (serviceLevel: string): Promise<Client[]> => {
    try {
      const response = await axiosInstance.get(`/clients/service-level/${serviceLevel}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Obtener clientes por ejecutivo de cuenta
  getClientsByManager: async (manager: string): Promise<Client[]> => {
    try {
      const response = await axiosInstance.get(`/clients/manager/${manager}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Obtener estadísticas del dashboard de clientes
  getDashboardStats: async (): Promise<ClientDashboardStats> => {
    try {
      const response = await axiosInstance.get('/clients/dashboard/stats');
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};

export default ClientService;