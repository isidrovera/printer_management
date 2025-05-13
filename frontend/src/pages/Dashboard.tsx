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
  PieChart,
  Settings,
  LayoutDashboard,
  BookOpen,
  LogOut,
  ArrowUpRight,
  HardDrive,
  BellRing
} from 'lucide-react';

const Dashboard = () => {
  // Hooks de navegación y autenticación
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  // Estado para datos del dashboard
  const [stats, setStats] = useState({
    printers: { total: 0, online: 0, offline: 0, error: 0 },
    clients: { total: 0, active: 0 },
    agents: { total: 0, online: 0, offline: 0 },
    tunnels: { total: 0, active: 0 }
  });
  
  // Estados para UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activePage, setActivePage] = useState('dashboard');

  // Función para obtener datos
  const fetchStats = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setRefreshing(true);

      // Llamada real a la API
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

  // Efecto para cargar datos iniciales
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

  // Manejador para actualizar manualmente
  const handleRefresh = () => {
    fetchStats(false);
  };

  // Manejador de cierre de sesión
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Cálculo del porcentaje de dispositivos en línea
  const calculateOnlinePercentage = () => {
    const totalDevices = stats.printers.total + stats.agents.total;
    const onlineDevices = stats.printers.online + stats.agents.online;
    return totalDevices > 0 ? Math.round((onlineDevices / totalDevices) * 100) : 0;
  };

  const onlinePercentage = calculateOnlinePercentage();

  // Pantalla de carga
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

  // Componente para los elementos de la sidebar
  const SidebarItem = ({ icon: Icon, label, path, active }) => {
    return (
      <div 
        className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all ${active ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50 text-gray-700'}`}
        onClick={() => navigate(path)}
      >
        <Icon className={`h-5 w-5 ${active ? 'text-blue-600' : 'text-gray-500'}`} />
        <span className={`${active ? 'font-medium' : ''}`}>{label}</span>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - Solo navegación lateral */}
      <div className="w-64 bg-white border-r border-gray-200 p-4 flex flex-col h-screen">
        <div className="flex items-center mb-6">
          <div className="text-blue-600 font-bold text-2xl">
            <span className="flex items-center">
              <Printer className="h-6 w-6 mr-2" />
              PrinterManager
            </span>
          </div>
        </div>
        
        <div className="bg-gray-100 p-2 rounded-lg flex items-center space-x-3 mb-6">
          <div className="bg-blue-500 h-8 w-8 rounded-lg flex items-center justify-center text-white font-medium">
            {user?.username ? user.username.substring(0, 2).toUpperCase() : 'JF'}
          </div>
          <div>
            <p className="text-sm font-medium">{user?.username || 'Jayden Frankie'}</p>
          </div>
        </div>
        
        <nav className="flex-1 space-y-1">
          <SidebarItem 
            icon={LayoutDashboard} 
            label="Dashboard" 
            path="/dashboard" 
            active={activePage === 'dashboard'} 
          />
          <SidebarItem 
            icon={Printer} 
            label="Monitoreo" 
            path="/printers" 
            active={window.location.pathname === '/printers'} 
          />
          <SidebarItem 
            icon={Users} 
            label="Clientes" 
            path="/clients" 
            active={window.location.pathname === '/clients'} 
          />
          <SidebarItem 
            icon={Network} 
            label="Agentes" 
            path="/agents" 
            active={window.location.pathname === '/agents'} 
          />
          <SidebarItem 
            icon={HardDrive} 
            label="Drivers" 
            path="/drivers" 
            active={window.location.pathname === '/drivers'} 
          />
          <SidebarItem 
            icon={Settings} 
            label="OIDs" 
            path="/printer-oids" 
            active={window.location.pathname === '/printer-oids'} 
          />
          <SidebarItem 
            icon={BookOpen} 
            label="Reportes" 
            path="/reports" 
            active={window.location.pathname === '/reports'} 
          />
        </nav>
        
        <div className="mt-auto pt-4 border-t border-gray-200">
          <div 
            className="flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all hover:bg-gray-50 text-gray-700"
            onClick={handleLogout}
          >
            <LogOut className="h-5 w-5 text-gray-500" />
            <span>Cerrar sesión</span>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-6">
          {/* Header del Dashboard */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Hola, Welcome back</h1>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="relative">
                <select className="appearance-none bg-white border border-gray-200 rounded-lg py-2 pl-3 pr-10 focus:outline-none">
                  <option>🇪🇸 ES</option>
                  <option>🇬🇧 EN</option>
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                  <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              
              <button className="relative bg-white p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
                <BellRing className="h-5 w-5 text-gray-500" />
                <span className="absolute -top-0.5 -right-0.5 h-2 w-2 bg-red-500 rounded-full"></span>
              </button>
              
              <button 
                onClick={handleRefresh}
                disabled={refreshing}
                className="bg-white p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <RefreshCcw className={`h-5 w-5 text-gray-500 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
              
              <div className="bg-orange-100 h-8 w-8 rounded-lg flex items-center justify-center text-orange-800 font-medium">
                {user?.username ? user.username.substring(0, 2).toUpperCase() : 'JF'}
              </div>
            </div>
          </div>
          
          {/* Tarjetas de estadísticas */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Tarjeta 1 */}
            <div 
              className="bg-blue-50 rounded-xl p-6 flex flex-col items-center cursor-pointer transition-all hover:shadow-md"
              onClick={() => navigate('/stats_weekly')}
            >
              <div className="p-3 rounded-full bg-white bg-opacity-30 mb-4">
                <BarChart3 className="h-6 w-6 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-blue-600">{stats.printers?.total > 0 ? "714k" : "0"}</h2>
              <p className="text-blue-600 text-sm opacity-90">Impresiones Semanales</p>
            </div>
            
            {/* Tarjeta 2 */}
            <div 
              className="bg-green-50 rounded-xl p-6 flex flex-col items-center cursor-pointer transition-all hover:shadow-md"
              onClick={() => navigate('/clients')}
            >
              <div className="p-3 rounded-full bg-white bg-opacity-30 mb-4">
                <Users className="h-6 w-6 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-green-600">{stats.clients?.total > 0 ? "1.35m" : "0"}</h2>
              <p className="text-green-600 text-sm opacity-90">Usuarios Nuevos</p>
            </div>
            
            {/* Tarjeta 3 */}
            <div 
              className="bg-yellow-50 rounded-xl p-6 flex flex-col items-center cursor-pointer transition-all hover:shadow-md"
              onClick={() => navigate('/printers')}
            >
              <div className="p-3 rounded-full bg-white bg-opacity-30 mb-4">
                <Printer className="h-6 w-6 text-yellow-600" />
              </div>
              <h2 className="text-2xl font-bold text-yellow-600">{stats.printers?.total > 0 ? "1.72m" : "0"}</h2>
              <p className="text-yellow-600 text-sm opacity-90">Total Impresoras</p>
            </div>
            
            {/* Tarjeta 4 */}
            <div 
              className="bg-red-50 rounded-xl p-6 flex flex-col items-center cursor-pointer transition-all hover:shadow-md"
              onClick={() => navigate('/reports')}
            >
              <div className="p-3 rounded-full bg-white bg-opacity-30 mb-4">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <h2 className="text-2xl font-bold text-red-600">234</h2>
              <p className="text-red-600 text-sm opacity-90">Bug Reports</p>
            </div>
          </div>
          
          {/* Estado general del sistema */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg mb-6 flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          
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
          
          {/* Gráficos */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gráfico de actividad */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">Actividad Impresoras</h2>
                  <p className="text-sm text-gray-500">+14.5% más que el año pasado</p>
                </div>
                <button 
                  className="text-blue-600 text-sm font-medium flex items-center"
                  onClick={() => navigate('/printer_activity')}
                >
                  Ver detalles
                  <ArrowUpRight className="h-4 w-4 ml-1" />
                </button>
              </div>
              
              <div className="flex mb-4 space-x-4">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-blue-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Team A</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-yellow-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Team B</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-green-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Team C</span>
                </div>
              </div>
              
              {/* Gráfico simplificado */}
              <div className="h-64 flex items-end space-x-2">
                {[40, 20, 60, 30, 50, 25, 70, 35, 55, 45, 65, 30].map((height, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    {index % 3 === 0 && (
                      <div 
                        className="w-full mb-2 rounded-sm"
                        style={{ 
                          height: `${height * 0.6}%`,
                          backgroundColor: '#4285F4'
                        }}
                      ></div>
                    )}
                    <div
                      className="w-full relative group"
                      style={{ height: `${height}%` }}
                    >
                      <div className="w-full absolute bottom-0 left-0 bg-blue-100 rounded-sm">
                        <div 
                          className="absolute bottom-0 left-0 w-full bg-blue-500 rounded-sm transition-all duration-300"
                          style={{ height: '100%' }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex justify-between mt-4">
                <span className="text-xs text-gray-500">Ene</span>
                <span className="text-xs text-gray-500">Feb</span>
                <span className="text-xs text-gray-500">Mar</span>
                <span className="text-xs text-gray-500">Abr</span>
                <span className="text-xs text-gray-500">May</span>
                <span className="text-xs text-gray-500">Jun</span>
                <span className="text-xs text-gray-500">Jul</span>
                <span className="text-xs text-gray-500">Ago</span>
                <span className="text-xs text-gray-500">Sep</span>
                <span className="text-xs text-gray-500">Oct</span>
                <span className="text-xs text-gray-500">Nov</span>
                <span className="text-xs text-gray-500">Dic</span>
              </div>
            </div>
            
            {/* Gráfico de distribución */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">Distribución Clientes</h2>
                  <p className="text-sm text-gray-500">Actual</p>
                </div>
                <button 
                  className="text-blue-600 text-sm font-medium flex items-center"
                  onClick={() => navigate('/client_distribution')}
                >
                  Ver detalles
                  <ArrowUpRight className="h-4 w-4 ml-1" />
                </button>
              </div>
              
              <div className="flex justify-center">
                <div className="w-64 h-64 relative">
                  {/* Simple pie chart representation */}
                  <div className="relative">
                    <svg viewBox="0 0 100 100" className="w-full h-full">
                      {/* Blue segment - 27% */}
                      <path 
                        d="M50,50 L97,50 A47,47 0 0,1 85.35,85.35 Z" 
                        fill="#4285F4"
                      />
                      
                      {/* Red segment - 34% */}
                      <path 
                        d="M50,50 L85.35,85.35 A47,47 0 0,1 33.98,96.98 Z" 
                        fill="#EA4335"
                      />
                      
                      {/* Yellow segment - 13% */}
                      <path 
                        d="M50,50 L33.98,96.98 A47,47 0 0,1 3,50 Z" 
                        fill="#FBBC05"
                      />
                      
                      {/* Green segment - 26% */}
                      <path 
                        d="M50,50 L3,50 A47,47 0 0,1 50,3 L50,50 Z" 
                        fill="#34A853"
                      />
                      
                      <circle cx="50" cy="50" r="30" fill="white" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-blue-500 mr-2"></div>
                  <span className="text-sm text-gray-600">América (27%)</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-red-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Asia (34%)</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-yellow-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Europa (13%)</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-green-500 mr-2"></div>
                  <span className="text-sm text-gray-600">África (26%)</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Última actualización */}
          <div className="mt-8 text-center text-gray-500 text-sm">
            Última actualización: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;