import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
      const response = await axios.get(`${API_URL}/clients`, {
        params: { search, status },
      });
      return response.data.clients || [];
    } catch (error) {
      console.error("Error fetching clients:", error);
      throw error;
    }
  }

  static async getClientById(clientId: number): Promise<Client | null> {
    try {
      const response = await axios.get(`${API_URL}/clients/${clientId}/details`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching client ${clientId}:`, error);
      return null;
    }
  }

  static async createClient(clientData: Client): Promise<Client> {
    try {
      const response = await axios.post(`${API_URL}/clients/create`, clientData);
      return response.data;
    } catch (error) {
      console.error("Error creating client:", error);
      throw error;
    }
  }

  static async updateClient(clientId: number, clientData: Client): Promise<Client> {
    try {
      const response = await axios.post(`${API_URL}/clients/${clientId}/edit`, clientData);
      return response.data;
    } catch (error) {
      console.error(`Error updating client ${clientId}:`, error);
      throw error;
    }
  }

  static async deleteClient(clientId: number): Promise<boolean> {
    try {
      const response = await axios.delete(`${API_URL}/clients/${clientId}`);
      return response.data.success;
    } catch (error) {
      console.error(`Error deleting client ${clientId}:`, error);
      return false;
    }
  }
}
