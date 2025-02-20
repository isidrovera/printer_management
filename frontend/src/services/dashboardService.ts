import axiosInstance from '../utils/axios';

export interface DashboardStats {
  clients: {
    total: number;
    online: number;
    offline: number;
  };
  agents: {
    total: number;
    online: number;
    offline: number;
  };
  tunnels: {
    total: number;
    active: number;
  };
  printers: {
    total: number;
    online: number;
    offline: number;
  };
}

export const dashboardService = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await axiosInstance.get('/dashboard/stats');
    return response.data;
  },
};