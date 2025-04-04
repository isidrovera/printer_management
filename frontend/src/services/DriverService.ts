// src/services/DriverService.ts
import axiosInstance from '../lib/axios';

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
      const response = await axiosInstance.get(`/drivers`);
      return response.data;
    } catch (error) {
      console.error('Error fetching drivers', error);
      throw error;
    }
  },

  // Obtener driver por ID
  async getDriverById(driverId: number): Promise<Driver> {
    try {
      const response = await axiosInstance.get(`/drivers/${driverId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching driver ${driverId}`, error);
      throw error;
    }
  },

  // Eliminar driver
  async deleteDriver(driverId: number): Promise<any> {
    try {
      const response = await axiosInstance.delete(`/drivers/${driverId}`);
      return response.data;
    } catch (error) {
      console.error(`Error deleting driver ${driverId}`, error);
      throw error;
    }
  },

  // Obtener URL de descarga de un driver
  getDriverDownloadUrl(driverId: number): string {
    return `${axiosInstance.defaults.baseURL}/drivers/agents/drivers/download/${driverId}`;
  }
};

export default DriverService;