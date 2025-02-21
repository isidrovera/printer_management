// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';
import { 
  Printer, 
  Users, 
  Network, 
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState({
    printers: { total: 0, online: 0, error: 0 },
    clients: { total: 0, active: 0 },
    agents: { total: 0, online: 0, offline: 0 },
    tunnels: { total: 0, active: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get('/api/v1/dashboard/stats');
        setStats(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard stats:', err);
        setError('Error al cargar las estadísticas');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
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
                  <span>Error: {stats.printers.error}</span>
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
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Activos: {stats.clients.active}</span>
                </div>
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

        {/* Alertas */}
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