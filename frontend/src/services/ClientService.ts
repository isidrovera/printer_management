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
      // Usar el endpoint de búsqueda específico si hay un término
      if (search && search.trim() !== '') {
        console.log(`Usando endpoint de búsqueda con término: ${search}`);
        const response = await axiosInstance.get(`/clients/search/${encodeURIComponent(search)}`);
        return response.data || [];
      } 
      // Usar el endpoint de estado específico si hay un filtro de estado
      else if (status && status.trim() !== '') {
        console.log(`Usando endpoint de estado con valor: ${status}`);
        const response = await axiosInstance.get(`/clients/status/${encodeURIComponent(status)}`);
        return response.data || [];
      } 
      // Para obtener todos los clientes, usamos un enfoque alternativo
      else {
        console.log('Obteniendo todos los clientes sin filtros');
        
        // Intentar con un valor dummy para el parámetro search (esto podría evitar la validación 422)
        const response = await axiosInstance.get('/clients/', { 
          params: { 
            dummy: 'all' 
          } 
        });
        
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