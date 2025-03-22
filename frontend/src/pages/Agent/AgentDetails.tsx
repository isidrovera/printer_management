import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { AgentService, Agent } from '../../services/AgentService';
import { ArrowLeft, Edit, Trash2, Laptop, Server, Monitor, Clipboard } from 'lucide-react';

const AgentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  useEffect(() => {
    loadAgent();
  }, [id]);

  const loadAgent = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const data = await AgentService.getAgentById(parseInt(id));
      setAgent(data);
    } catch (error) {
      console.error('Error al cargar el agente', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!agent?.id) return;
    
    try {
      await AgentService.deleteAgent(agent.id);
      navigate('/agents');
    } catch (error) {
      console.error('Error al eliminar el agente', error);
    }
  };

  const copyToClipboard = () => {
    if (!agent?.token) return;
    
    navigator.clipboard.writeText(agent.token)
      .then(() => {
        setCopiedToken(true);
        setTimeout(() => setCopiedToken(false), 2000);
      })
      .catch(err => console.error('Error al copiar token', err));
  };

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType.toLowerCase()) {
      case 'desktop':
        return <Monitor size={24} className="mr-2" />;
      case 'server':
        return <Server size={24} className="mr-2" />;
      default:
        return <Laptop size={24} className="mr-2" />;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-pulse text-gray-400">Cargando...</div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="mb-6">
          <Link to="/agents" className="text-blue-500 hover:underline flex items-center">
            <ArrowLeft size={18} className="mr-1" /> Volver a la lista
          </Link>
        </div>
        <div className="bg-white p-8 rounded-lg shadow-sm text-center">
          <h2 className="text-xl font-medium mb-4">Agente no encontrado</h2>
          <p className="text-gray-600 mb-6">El agente que estás buscando no existe o ha sido eliminado.</p>
          <Link to="/agents" className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors">
            Volver a agentes
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex justify-between items-center">
        <Link to="/agents" className="text-blue-500 hover:underline flex items-center">
          <ArrowLeft size={18} className="mr-1" /> Volver a la lista
        </Link>
        <div className="flex space-x-2">
          <Link 
            to={`/agents/${agent.id}/edit`}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors flex items-center"
          >
            <Edit size={18} className="mr-1" /> Editar
          </Link>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md transition-colors flex items-center"
          >
            <Trash2 size={18} className="mr-1" /> Eliminar
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="p-6 border-b">
          <div className="flex items-center">
            {getDeviceIcon(agent.device_type)}
            <h1 className="text-2xl font-medium">{agent.hostname}</h1>
          </div>
          <div className="mt-2">
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
              agent.status === 'active' ? 'bg-green-100 text-green-800' : 
              agent.status === 'inactive' ? 'bg-red-100 text-red-800' : 
              'bg-gray-100 text-gray-800'
            }`}>
              {agent.status === 'active' ? 'Activo' : 
               agent.status === 'inactive' ? 'Inactivo' : agent.status}
            </span>
          </div>
        </div>

        <div className="p-6">
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <dt className="text-sm font-medium text-gray-500 mb-1">Token</dt>
              <dd className="flex items-center">
                <code className="p-2 bg-gray-50 rounded text-sm font-mono break-all flex-grow">{agent.token}</code>
                <button 
                  onClick={copyToClipboard}
                  className="ml-2 p-2 text-gray-400 hover:text-blue-500 transition-colors"
                  title="Copiar token"
                >
                  <Clipboard size={18} />
                </button>
                {copiedToken && (
                  <span className="ml-2 text-xs text-green-600">¡Copiado!</span>
                )}
              </dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500 mb-1">Nombre de host</dt>
              <dd>{agent.hostname}</dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500 mb-1">Nombre de usuario</dt>
              <dd>{agent.username}</dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500 mb-1">Dirección IP</dt>
              <dd>{agent.ip_address}</dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500 mb-1">Tipo de dispositivo</dt>
              <dd>{agent.device_type}</dd>
            </div>

            <div className="md:col-span-2">
              <dt className="text-sm font-medium text-gray-500 mb-1">Información del sistema</dt>
              <dd className="p-3 bg-gray-50 rounded-md">
                <pre className="text-xs overflow-auto whitespace-pre-wrap">
                  {JSON.stringify(agent.system_info, null, 2)}
                </pre>
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Modal de eliminación */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h2 className="text-xl font-medium mb-3">¿Eliminar agente?</h2>
            <p className="mb-4 text-gray-600">
              ¿Estás seguro de eliminar el agente <span className="font-medium">{agent.hostname}</span>? Esta acción no se puede deshacer.
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

export default AgentDetail;