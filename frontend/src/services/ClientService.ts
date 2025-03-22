// src/services/ClientService.ts
import axiosInstance from '../lib/axios';

export interface Client {
  id?: number;
  name: string;
  business_name?: string;
  tax_id?: string;
  client_type?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  status?: string;
}

export class ClientService {
  static async getClients(search?: string, status?: string): Promise<Client[]> {
    try {
      // Primero, verifica si estás usando los endpoints específicos
      if (search && !status) {
        // Endpoint específico de búsqueda
        const response = await axiosInstance.get(`/clients/search/${search}`);
        return response.data || [];
      } else if (status && !search) {
        // Endpoint específico de estado
        const response = await axiosInstance.get(`/clients/status/${status}`);
        return response.data || [];
      } else {
        // Ruta principal con parámetros de consulta opcionales
        let url = '/clients';
        const params: Record<string, string> = {};
        
        if (search) params.search = search;
        if (status) params.status = status;
        
        const response = await axiosInstance.get(url, { params });
        return response.data || [];
      }
    } catch (error) {
      console.error("Error fetching clients:", error);
      throw error;
    }
  }
  

  static async getClientById(clientId: number): Promise<Client | null> {
    try {
      const response = await axiosInstance.get(`/clients/${clientId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching client ${clientId}:`, error);
      return null;
    }
  }

  static async createClient(clientData: Client): Promise<Client> {
    try {
      const response = await axiosInstance.post('/clients', clientData);
      return response.data;
    } catch (error) {
      console.error("Error creating client:", error);
      throw error;
    }
  }

  static async updateClient(clientId: number, clientData: Partial<Client>): Promise<Client> {
    try {
      const response = await axiosInstance.put(`/clients/${clientId}`, clientData);
      return response.data;
    } catch (error) {
      console.error(`Error updating client ${clientId}:`, error);
      throw error;
    }
  }

  static async deleteClient(clientId: number): Promise<boolean> {
    try {
      await axiosInstance.delete(`/clients/${clientId}`);
      return true;
    } catch (error) {
      console.error(`Error deleting client ${clientId}:`, error);
      return false;
    }
  }

  static async searchClients(searchTerm: string): Promise<Client[]> {
    try {
      const response = await axiosInstance.get(`/clients/search/${searchTerm}`);
      return response.data || [];
    } catch (error) {
      console.error("Error searching clients:", error);
      throw error;
    }
  }
}