// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';
import { 
  Printer, 
  Users, 
  Network, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react';
import axios from 'axios';

interface DashboardStats {
  printers: {
    total: number;
    online: number;
    offline: number;
    last_updated?: string;
  };
  clients: {
    total: number;
    last_updated?: string;
  };
  agents: {
    total: number;
    online: number;
    offline: number;
    last_updated?: string;
  };
  tunnels: {
    total: number;
    active: number;
    last_updated?: string;
  };
}

const initialStats: DashboardStats = {
  printers: { total: 0, online: 0, offline: 0 },
  clients: { total: 0 },
  agents: { total: 0, online: 0, offline: 0 },
  tunnels: { total: 0, active: 0 }
};

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats>(initialStats);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/v1/dashboard/stats');
        
        if (response.data) {
          setStats(response.data);
          setError(null);
        }
      } catch (err) {
        console.error('Error fetching dashboard stats:', err);
        setError('Error al cargar las estadísticas');
        // Mantener los stats anteriores en caso de error
      } finally {
        setLoading(false);
      }
    };

    fetchStats();

    // Actualizar cada 30 segundos
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6 flex items-center">
          <AlertTriangle className="h-5 w-5 mr-2" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Impresoras */}
        <Card className="p-6">
          <div className="flex items-center">
            <Printer className="h-10 w-10 text-blue-600" />
            <div className="ml-4">
              <h2 className="text-lg font-semibold">Impresoras</h2>
              <div className="mt-2 space-y-1">
                <div className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Online: {stats.printers.online}</span>
                </div>
                <div className="flex items-center">
                  <XCircle className="h-4 w-4 text-red-500 mr-2" />
                  <span>Offline: {stats.printers.offline}</span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Total: {stats.printers.total}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Clientes */}
        <Card className="p-6">
          <div className="flex items-center">
            <Users className="h-10 w-10 text-blue-600" />
            <div className="ml-4">
              <h2 className="text-lg font-semibold">Clientes</h2>
              <div className="mt-2 space-y-1">
                <div className="flex items-center">
                  <span className="font-medium">Total: {stats.clients.total}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Agentes */}
        <Card className="p-6">
          <div className="flex items-center">
            <Network className="h-10 w-10 text-blue-600" />
            <div className="ml-4">
              <h2 className="text-lg font-semibold">Agentes</h2>
              <div className="mt-2 space-y-1">
                <div className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Online: {stats.agents.online}</span>
                </div>
                <div className="flex items-center">
                  <XCircle className="h-4 w-4 text-red-500 mr-2" />
                  <span>Offline: {stats.agents.offline}</span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Total: {stats.agents.total}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Túneles */}
        <Card className="p-6">
          <div className="flex items-center">
            <AlertTriangle className="h-10 w-10 text-yellow-500" />
            <div className="ml-4">
              <h2 className="text-lg font-semibold">Estado</h2>
              <div className="mt-2 space-y-1">
                <div className="flex items-center">
                  <Network className="h-4 w-4 text-blue-500 mr-2" />
                  <span>Túneles Activos: {stats.tunnels.active}</span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Total Túneles: {stats.tunnels.total}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;