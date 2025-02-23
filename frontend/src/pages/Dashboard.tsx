// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '@/components/ui/card';
import axiosInstance from '../lib/axios';
import { 
  Printer, 
  Users, 
  Network, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCcw
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DashboardStats {
  printers: {
    total: number;
    online: number;
    offline: number;
    error: number;
    last_updated?: string;
  };
  clients: {
    total: number;
    active: number;
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
  printers: { total: 0, online: 0, offline: 0, error: 0 },
  clients: { total: 0, active: 0 },
  agents: { total: 0, online: 0, offline: 0 },
  tunnels: { total: 0, active: 0 }
};

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats>(initialStats);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const fetchStats = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setRefreshing(true);

      const response = await axiosInstance.get('/dashboard/stats');
      
      if (response.data) {
        // Asegurarse de que los datos tengan la estructura correcta
        const safeStats = {
          printers: {
            total: response.data?.printers?.total ?? 0,
            online: response.data?.printers?.online ?? 0,
            offline: response.data?.printers?.offline ?? 0,
            error: response.data?.printers?.error ?? 0
          },
          clients: {
            total: response.data?.clients?.total ?? 0,
            active: response.data?.clients?.active ?? 0
          },
          agents: {
            total: response.data?.agents?.total ?? 0,
            online: response.data?.agents?.online ?? 0,
            offline: response.data?.agents?.offline ?? 0
          },
          tunnels: {
            total: response.data?.tunnels?.total ?? 0,
            active: response.data?.tunnels?.active ?? 0
          }
        };
        setStats(safeStats);
        setError(null);
      }
    } catch (err: any) {
      console.error('Error fetching dashboard stats:', err);
      
      if (err.response?.status === 401 || err.response?.status === 303) {
        await logout();
        navigate('/login');
        return;
      }
      
      setError('Error al cargar las estadísticas del dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();

    if (mounted) {
      fetchStats();
    }

    // Actualizar cada 30 segundos
    const interval = setInterval(() => {
      if (mounted) {
        fetchStats(false);
      }
    }, 30000);

    return () => {
      mounted = false;
      controller.abort();
      clearInterval(interval);
    };
  }, [logout, navigate]);

  const handleRefresh = () => {
    fetchStats(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <Button 
          onClick={handleRefresh} 
          variant="outline"
          disabled={refreshing}
          className="flex items-center gap-2"
        >
          <RefreshCcw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

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
                  <AlertTriangle className="h-4 w-4 text-yellow-500 mr-2" />
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