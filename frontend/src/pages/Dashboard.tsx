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
  RefreshCcw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

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
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const fetchStats = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setRefreshing(true);
      const response = await axiosInstance.get('/dashboard/stats');
      setStats(response.data);
      setError(null);
    } catch (err) {
      if (err.response?.status === 401) {
        await logout();
        navigate('/login');
        return;
      }
      setError('Error al cargar las estadísticas');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(() => fetchStats(false), 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-4xl font-bold text-gray-900">Dashboard</h1>
        <Button onClick={() => fetchStats(false)} variant="outline" disabled={refreshing}>
          <RefreshCcw className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-red-50 text-red-700 p-4 rounded-lg mb-6 flex items-center">
          <AlertTriangle className="h-5 w-5 mr-2" />
          {error}
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: 'Impresoras', icon: Printer, data: stats?.printers },
          { title: 'Clientes', icon: Users, data: stats?.clients },
          { title: 'Agentes', icon: Network, data: stats?.agents },
          { title: 'Túneles', icon: AlertTriangle, data: stats?.tunnels },
        ].map(({ title, icon: Icon, data }, index) => (
          <motion.div key={index} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <Card className="p-6 shadow-lg hover:shadow-2xl transition-shadow duration-300">
              <div className="flex items-center">
                <Icon className="h-10 w-10 text-blue-600" />
                <div className="ml-4">
                  <h2 className="text-lg font-semibold">{title}</h2>
                  <div className="mt-2 space-y-1">
                    {Object.entries(data || {}).map(([key, value]) => (
                      <div key={key} className="flex items-center">
                        <span className="font-medium capitalize">{key}: {value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
