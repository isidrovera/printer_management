import { useEffect, useState } from 'react';
import { dashboardService, DashboardStats } from '../services/dashboardService';
import MainLayout from '../layouts/MainLayout';
import { Printer, Users, Network, Server } from 'lucide-react';

const StatCard = ({ title, total, online, offline, icon: Icon }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg">
    <div className="p-5">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-6 w-6 text-gray-400" />
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
            <dd>
              <div className="text-lg font-medium text-gray-900">{total}</div>
            </dd>
          </dl>
        </div>
      </div>
    </div>
    <div className="bg-gray-50 px-5 py-3">
      <div className="text-sm">
        <span className="text-green-700 mr-2">{online} en línea</span>
        {offline > 0 && <span className="text-red-700">{offline} offline</span>}
      </div>
    </div>
  </div>
);

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await dashboardService.getStats();
        setStats(data);
      } catch (err) {
        setError('Error al cargar las estadísticas');
        console.error('Error fetching stats:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Actualizar cada 30 segundos

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-lg">Cargando estadísticas...</div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <div className="bg-red-50 p-4 rounded-md">
          <div className="text-red-700">{error}</div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {stats && (
            <>
              <StatCard
                title="Clientes"
                total={stats.clients.total}
                online={stats.clients.online}
                offline={stats.clients.offline}
                icon={Users}
              />
              <StatCard
                title="Agentes"
                total={stats.agents.total}
                online={stats.agents.online}
                offline={stats.agents.offline}
                icon={Server}
              />
              <StatCard
                title="Túneles"
                total={stats.tunnels.total}
                online={stats.tunnels.active}
                offline={stats.tunnels.total - stats.tunnels.active}
                icon={Network}
              />
              <StatCard
                title="Impresoras"
                total={stats.printers.total}
                online={stats.printers.online}
                offline={stats.printers.offline}
                icon={Printer}
              />
            </>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default Dashboard;