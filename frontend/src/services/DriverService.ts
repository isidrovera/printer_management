// src/services/DriverService.ts
import axios from 'axios';
import { API_BASE_URL } from '../config';

// Tipos
export interface Driver {
  id: number;
  manufacturer: string;
  model: string;
  driver_filename: string;
  description?: string;
}

// Servicio
export const DriverService = {
  // Obtener todos los drivers
  async getDrivers(): Promise<Driver[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/drivers`);
      return response.data;
    } catch (error) {
      console.error('Error fetching drivers', error);
      throw error;
    }
  },

  // Obtener driver por ID
  async getDriverById(driverId: number): Promise<Driver> {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/drivers/${driverId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching driver ${driverId}`, error);
      throw error;
    }
  },

  // Eliminar driver
  async deleteDriver(driverId: number): Promise<any> {
    try {
      const response = await axios.delete(`${API_BASE_URL}/api/v1/drivers/${driverId}`);
      return response.data;
    } catch (error) {
      console.error(`Error deleting driver ${driverId}`, error);
      throw error;
    }
  },

  // Obtener URL de descarga de un driver
  getDriverDownloadUrl(driverId: number): string {
    return `${API_BASE_URL}/api/v1/drivers/agents/drivers/download/${driverId}`;
  }
};

export default DriverService;