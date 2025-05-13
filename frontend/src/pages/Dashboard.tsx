// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
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
  BarChart3,
  Settings
} from 'lucide-react';

// Componente de tarjeta personalizada
const StatsCard = ({ icon: Icon, title, stats, color }) => {
  return (
    <div className={`bg-white rounded-xl shadow-sm border-l-4 ${color} p-5 transition-all hover:shadow-md`}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h2 className="text-lg font-medium text-gray-700">{title}</h2>
          <div className="mt-4 space-y-2">
            {Object.entries(stats).map(([key, value], index) => {
              if (key !== 'total' && key !== 'last_updated') {
                const Icon = 
                  key === 'online' || key === 'active' ? CheckCircle :
                  key === 'offline' ? XCircle :
                  key === 'error' ? AlertTriangle : null;
                
                const textColor = 
                  key === 'online' || key === 'active' ? 'text-green-600' :
                  key === 'offline' ? 'text-red-600' :
                  key === 'error' ? 'text-amber-600' : 'text-gray-700';
                
                return (
                  <div key={index} className="flex items-center">
                    {Icon && <Icon className={`h-4 w-4 ${textColor} mr-2`} />}
                    <span className={`${textColor} capitalize`}>
                      {key}: <span className="font-medium">{value}</span>
                    </span>
                  </div>
                );
              }
              return null;
            })}
            <div className="pt-2 mt-2 border-t border-gray-100">
              <span className="font-medium text-gray-800">Total: {stats.total}</span>
            </div>
          </div>
        </div>
        <div className={`p-3 rounded-full ${color.replace('border-l', 'bg').replace('-600', '-100')}`}>
          <Icon className={`h-6 w-6 ${color.replace('border-l', 'text')}`} />
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [stats, setStats] = useState({
    printers: { total: 0, online: 0, offline: 0, error: 0 },
    clients: { total: 0, active: 0 },
    agents: { total: 0, online: 0, offline: 0 },
    tunnels: { total: 0, active: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const fetchStats = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setRefreshing(true);

      const response = await axiosInstance.get('/dashboard/stats');
      
      if (response.data) {
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
    } catch (err) {
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
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Cargando estadísticas...</p>
        </div>
      </div>
    );
  }

  // Calcular el porcentaje de dispositivos en línea
  const calculateOnlinePercentage = () => {
    const totalDevices = stats.printers.total + stats.agents.total;
    const onlineDevices = stats.printers.online + stats.agents.online;
    return totalDevices > 0 ? Math.round((onlineDevices / totalDevices) * 100) : 0;
  };

  const onlinePercentage = calculateOnlinePercentage();

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
            <p className="text-gray-500 mt-1">Monitoreo de dispositivos y servicios</p>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 py-2 px-4 bg-white border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <RefreshCcw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Actualizar</span>
            </button>
            
            <button className="p-2 bg-white border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
              <Settings className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        {/* Estado general */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-sm p-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-medium text-gray-700">Estado general del sistema</h2>
                <p className="text-gray-500 text-sm mt-1">
                  {onlinePercentage >= 80 ? 'Funcionando correctamente' : 
                   onlinePercentage >= 50 ? 'Funcionamiento parcial' : 'Problemas críticos'}
                </p>
              </div>
              <div className="flex items-center">
                <div className="w-16 h-16 rounded-full border-4 border-gray-100 flex items-center justify-center">
                  <div className="text-xl font-bold" style={{color: 
                    onlinePercentage >= 80 ? '#10b981' : 
                    onlinePercentage >= 50 ? '#f59e0b' : '#ef4444'}}>
                    {onlinePercentage}%
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-4 bg-gray-100 rounded-full h-3">
              <div 
                className={`h-3 rounded-full ${
                  onlinePercentage >= 80 ? 'bg-green-500' : 
                  onlinePercentage >= 50 ? 'bg-amber-500' : 'bg-red-500'
                }`}
                style={{ width: `${onlinePercentage}%` }}
              ></div>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg mb-6 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Tarjetas de estadísticas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard 
            icon={Printer} 
            title="Impresoras" 
            stats={stats.printers} 
            color="border-l-blue-600" 
          />
          
          <StatsCard 
            icon={Users} 
            title="Clientes" 
            stats={stats.clients} 
            color="border-l-green-600" 
          />
          
          <StatsCard 
            icon={Network} 
            title="Agentes" 
            stats={stats.agents} 
            color="border-l-purple-600" 
          />
          
          <StatsCard 
            icon={BarChart3} 
            title="Túneles" 
            stats={stats.tunnels} 
            color="border-l-amber-600" 
          />
        </div>
        
        {/* Última actualización */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          Última actualización: {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;