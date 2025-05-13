// src/services/OIDService.ts
import axiosInstance from '../lib/axios';

export interface OID {
  id: number;
  name: string;
  oid: string;
  description: string;
  type: string;
}

class OIDService {
  // Endpoint base para los OIDs
  private endpoint = '/printer-oids';
  
  // Obtener todos los OIDs
  async getAll(): Promise<OID[]> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.get('https://copierconnectremote.com/api/v1/printer-oids');
      return response.data;
    } catch (error) {
      console.error('Error fetching OIDs:', error);
      throw error;
    }
  }
  
  // Obtener un OID por su ID
  async getById(id: number): Promise<OID> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.get(`https://copierconnectremote.com/api/v1/printer-oids/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching OID ${id}:`, error);
      throw error;
    }
  }
  
  // Crear un nuevo OID
  async create(data: Omit<OID, 'id'>): Promise<any> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.post('https://copierconnectremote.com/api/v1/printer-oids', data);
      return response.data;
    } catch (error) {
      console.error('Error creating OID:', error);
      throw error;
    }
  }
  
  // Actualizar un OID existente
  async update(id: number, data: Omit<OID, 'id'>): Promise<any> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.put(`https://copierconnectremote.com/api/v1/printer-oids/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating OID ${id}:`, error);
      throw error;
    }
  }
  
  // Eliminar un OID
  async delete(id: number): Promise<any> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.delete(`https://copierconnectremote.com/api/v1/printer-oids/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error deleting OID ${id}:`, error);
      throw error;
    }
  }
}

export default new OIDService();