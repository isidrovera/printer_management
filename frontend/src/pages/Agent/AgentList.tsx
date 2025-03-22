import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AgentService, Agent } from '../../services/AgentService';
import { Eye, Edit, Trash2, Plus, Search, X, Laptop, Server, Monitor } from 'lucide-react';

const AgentList = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    loadAgents();
  }, [searchTerm]);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await AgentService.getAgents(searchTerm);
      setAgents(data);
    } catch (error) {
      console.error('Error al cargar los agentes', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedAgent?.id) return;
    try {
      await AgentService.deleteAgent(selectedAgent.id);
      setAgents(agents.filter(a => a.id !== selectedAgent.id));
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Error al eliminar el agente', error);
    }
  };

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType.toLowerCase()) {
      case 'desktop':
        return <Monitor size={18} />;
      case 'server':
        return <Server size={18} />;
      default:
        return <Laptop size={18} />;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-pulse text-gray-400">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-light text-gray-800">Agentes</h1>
        <Link 
          to="/agents/create" 
          className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-full transition-colors shadow-sm flex items-center"
          title="Nuevo Agente"
        >
          <Plus size={20} />
        </Link>
      </div>

      <div className="relative mb-6">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={18} className="text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Buscar agentes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 p-3 border-0 border-b focus:ring-0 focus:border-blue-500 transition-colors bg-gray-50 rounded-lg"
        />
        {searchTerm && (
          <button 
            onClick={() => setSearchTerm('')}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <X size={18} className="text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Hostname</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">IP</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-4 text-right font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {agents.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  No se encontraron agentes
                </td>
              </tr>
            ) : (
              agents.map((agent) => (
                <tr key={agent.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="mr-2 text-gray-500">
                        {getDeviceIcon(agent.device_type)}
                      </span>
                      {agent.hostname}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{agent.device_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{agent.ip_address}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      agent.status === 'active' ? 'bg-green-100 text-green-800' : 
                      agent.status === 'inactive' ? 'bg-red-100 text-red-800' : 
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {agent.status === 'active' ? 'Activo' : 
                       agent.status === 'inactive' ? 'Inactivo' : agent.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex justify-end gap-2">
                      <Link 
                        to={`/agents/${agent.id}`}
                        className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                        title="Ver detalles"
                      >
                        <Eye size={18} />
                      </Link>
                      <Link 
                        to={`/agents/${agent.id}/edit`}
                        className="p-1 text-gray-400 hover:text-green-500 transition-colors"
                        title="Editar agente"
                      >
                        <Edit size={18} />
                      </Link>
                      <button
                        onClick={() => {
                          setSelectedAgent(agent);
                          setShowDeleteModal(true);
                        }}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        title="Eliminar agente"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de eliminación */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h2 className="text-xl font-medium mb-3">¿Eliminar agente?</h2>
            <p className="mb-4 text-gray-600">
              ¿Estás seguro de eliminar el agente <span className="font-medium">{selectedAgent?.hostname}</span>? Esta acción no se puede deshacer.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md transition-colors"
              >
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentList;