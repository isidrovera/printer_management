// src/services/DriverService.ts
import axiosInstance from '../lib/axios';

export interface Driver {
  id: number;
  manufacturer: string;
  model: string;
  driver_filename: string;
  description: string;
}

class DriverService {
  // Endpoint base para los drivers
  private endpoint = '/drivers';
  
  // Obtener todos los drivers
  async getAll(): Promise<Driver[]> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.get('https://copierconnectremote.com/api/v1/drivers');
      return response.data;
    } catch (error) {
      console.error('Error fetching drivers:', error);
      throw error;
    }
  }
  
  // Obtener un driver por su ID
  async getById(id: number): Promise<Driver> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.get(`https://copierconnectremote.com/api/v1/drivers/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching driver ${id}:`, error);
      throw error;
    }
  }
  
  // Crear un nuevo driver
  async create(formData: FormData): Promise<any> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.post('https://copierconnectremote.com/api/v1/drivers', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error creating driver:', error);
      throw error;
    }
  }
  
  // Actualizar un driver existente
  async update(id: number, formData: FormData): Promise<any> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.put(`https://copierconnectremote.com/api/v1/drivers/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error(`Error updating driver ${id}:`, error);
      throw error;
    }
  }
  
  // Eliminar un driver
  async delete(id: number): Promise<any> {
    try {
      // Usar URL absoluta para evitar problemas de HTTPS
      const response = await axiosInstance.delete(`https://copierconnectremote.com/api/v1/drivers/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error deleting driver ${id}:`, error);
      throw error;
    }
  }
  
  // Obtener la URL de descarga de un driver
  getDownloadUrl(id: number): string {
    return `https://copierconnectremote.com/api/v1/drivers/agents/drivers/download/${id}`;
  }
}

export default new DriverService();