// src/services/TunnelService.ts
import axiosInstance from '../lib/axios';

// Tipos
export interface Tunnel {
  tunnel_id: string;
  remote_host: string;
  remote_port: number;
  local_port: number;
  ssh_host?: string;
  ssh_port?: number;
  status: string;
  description?: string;
  created_at?: string;
  agent?: {
    hostname: string;
    username: string;
    ip_address: string;
  };
}

export interface TunnelCreate {
  agent_id: number;
  remote_host: string;
  remote_port: number;
  local_port: number;
  ssh_host?: string;
  ssh_port?: number;
  username?: string;
  password?: string;
  description?: string;
}

// Servicio
export const TunnelService = {
  // Obtener todos los túneles con filtro opcional
  async getTunnels(search?: string): Promise<Tunnel[]> {
    try {
      const response = await axiosInstance.get(`/tunnels/list`, {
        params: { search }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching tunnels', error);
      throw error;
    }
  },

  // Obtener detalles de un túnel específico
  async getTunnelById(tunnelId: string): Promise<Tunnel> {
    try {
      const response = await axiosInstance.get(`/tunnels/${tunnelId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching tunnel ${tunnelId}`, error);
      throw error;
    }
  },

  // Crear un nuevo túnel
  async createTunnel(tunnelData: TunnelCreate): Promise<Tunnel> {
    try {
      const response = await axiosInstance.post(`/tunnels/create`, tunnelData);
      return response.data;
    } catch (error) {
      console.error('Error creating tunnel', error);
      throw error;
    }
  },

  // Cerrar un túnel existente
  async closeTunnel(tunnelId: string): Promise<any> {
    try {
      const response = await axiosInstance.delete(`/tunnels/${tunnelId}`);
      return response.data;
    } catch (error) {
      console.error(`Error closing tunnel ${tunnelId}`, error);
      throw error;
    }
  }
};

export default TunnelService;