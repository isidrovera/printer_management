// src/components/tunnels/TunnelList.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { TunnelService, Tunnel } from '../../services/TunnelService';
import { AgentService, Agent } from '../../services/AgentService';
import { 
  Eye, Edit, Trash2, Plus, Search, X, Terminal, 
  Server, Wifi, ExternalLink, Loader, Link2 
} from 'lucide-react';

// Definición de tipos
interface TunnelFormData {
  agent_id: number;
  remote_host: string;
  remote_port: number;
  local_port: number;
  ssh_host?: string;
  ssh_port?: number;
  username?: string;
  password?: string;
  description?: string;
}

const TunnelList = () => {
  // Estados
  const [tunnels, setTunnels] = useState<Tunnel[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTunnel, setSelectedTunnel] = useState<Tunnel | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState<TunnelFormData>({
    agent_id: 0,
    remote_host: '',
    remote_port: 22,
    local_port: 8022,
    ssh_host: '',
    ssh_port: 22,
    username: '',
    password: '',
    description: ''
  });
  const [formErrors, setFormErrors] = useState<{[key: string]: string}>({});
  const [createLoading, setCreateLoading] = useState(false);

  // Cargar datos iniciales
  useEffect(() => {
    loadTunnels();
    loadAgents();
  }, [searchTerm]);

  // Cargar túneles
  const loadTunnels = async () => {
    try {
      setLoading(true);
      const data = await TunnelService.getTunnels(searchTerm);
      setTunnels(data);
    } catch (error) {
      console.error('Error al cargar los túneles', error);
    } finally {
      setLoading(false);
    }
  };

  // Cargar agentes
  const loadAgents = async () => {
    try {
      const data = await AgentService.getAgents();
      // Filtrar solo agentes activos
      const activeAgents = data.filter(agent => agent.status === 'active');
      setAgents(activeAgents);
    } catch (error) {
      console.error('Error al cargar los agentes', error);
    }
  };

  // Manejar cierre de túnel
  const handleClose = async () => {
    if (!selectedTunnel?.tunnel_id) return;
    try {
      setLoading(true);
      await TunnelService.closeTunnel(selectedTunnel.tunnel_id);
      // Actualizar la lista
      loadTunnels();
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Error al cerrar el túnel', error);
    } finally {
      setLoading(false);
    }
  };

  // Manejar cambio en el formulario
  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    setFormData({
      ...formData,
      [name]: name === 'agent_id' || name === 'remote_port' || name === 'local_port' || name === 'ssh_port' 
        ? parseInt(value) 
        : value
    });
  };

  // Validar formulario
  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
    if (!formData.agent_id) {
      errors.agent_id = 'Selecciona un agente';
    }
    
    if (!formData.remote_host) {
      errors.remote_host = 'Ingresa la dirección del host remoto';
    }
    
    if (!formData.remote_port) {
      errors.remote_port = 'Ingresa el puerto remoto';
    }
    
    if (!formData.local_port) {
      errors.local_port = 'Ingresa el puerto local';
    }
    
    // Si se proporciona SSH, validar credenciales
    if (formData.ssh_host) {
      if (!formData.username) {
        errors.username = 'Ingresa el nombre de usuario SSH';
      }
      
      if (!formData.password) {
        errors.password = 'Ingresa la contraseña SSH';
      }
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Crear túnel
  const handleCreateTunnel = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      setCreateLoading(true);
      await TunnelService.createTunnel(formData);
      // Limpiar formulario y cerrar modal
      setFormData({
        agent_id: 0,
        remote_host: '',
        remote_port: 22,
        local_port: 8022,
        ssh_host: '',
        ssh_port: 22,
        username: '',
        password: '',
        description: ''
      });
      setShowCreateModal(false);
      // Recargar lista
      loadTunnels();
    } catch (error) {
      console.error('Error al crear el túnel', error);
      setFormErrors({
        submit: 'Error al crear el túnel. Verifica que el agente esté conectado.'
      });
    } finally {
      setCreateLoading(false);
    }
  };

  // Estado de carga
  if (loading && tunnels.length === 0) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-pulse text-gray-400">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-light text-gray-800">Túneles SSH</h1>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-full transition-colors shadow-sm flex items-center"
          title="Nuevo Túnel SSH"
        >
          <Plus size={20} />
        </button>
      </div>

      <div className="relative mb-6">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={18} className="text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Buscar túneles..."
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
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Agente</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Destino</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Puerto Local</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-4 text-right font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {tunnels.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  No se encontraron túneles activos
                </td>
              </tr>
            ) : (
              tunnels.map((tunnel) => (
                <tr key={tunnel.tunnel_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="mr-2 text-gray-500">
                        <Terminal size={18} />
                      </span>
                      {tunnel.agent?.hostname || 'Desconocido'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {tunnel.remote_host}:{tunnel.remote_port}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    localhost:{tunnel.local_port}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      tunnel.status === 'active' ? 'bg-green-100 text-green-800' : 
                      tunnel.status === 'creating' ? 'bg-blue-100 text-blue-800' :
                      tunnel.status === 'error' ? 'bg-red-100 text-red-800' : 
                      tunnel.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {tunnel.status === 'active' ? 'Activo' : 
                       tunnel.status === 'creating' ? 'Creando' :
                       tunnel.status === 'error' ? 'Error' :
                       tunnel.status === 'closed' ? 'Cerrado' : 
                       tunnel.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex justify-end gap-2">
                      {tunnel.status === 'active' && (
                        <a 
                          href={`http://localhost:${tunnel.local_port}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                          title="Abrir conexión"
                        >
                          <ExternalLink size={18} />
                        </a>
                      )}
                      <Link 
                        to={`/tunnels/${tunnel.tunnel_id}`}
                        className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                        title="Ver detalles"
                      >
                        <Eye size={18} />
                      </Link>
                      {tunnel.status !== 'closed' && (
                        <button
                          onClick={() => {
                            setSelectedTunnel(tunnel);
                            setShowDeleteModal(true);
                          }}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                          title="Cerrar túnel"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal para cerrar túnel */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h2 className="text-xl font-medium mb-3">¿Cerrar túnel SSH?</h2>
            <p className="mb-4 text-gray-600">
              ¿Estás seguro de cerrar el túnel hacia <span className="font-medium">{selectedTunnel?.remote_host}:{selectedTunnel?.remote_port}</span>? Esta acción cerrará la conexión.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleClose}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md transition-colors"
              >
                Cerrar túnel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal para crear túnel */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full">
            <h2 className="text-xl font-medium mb-4">Crear nuevo túnel SSH</h2>
            
            <form onSubmit={handleCreateTunnel}>
              {/* Selección de agente */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Agente
                </label>
                <select
                  name="agent_id"
                  value={formData.agent_id}
                  onChange={handleFormChange}
                  className={`w-full p-2 border rounded-md ${formErrors.agent_id ? 'border-red-500' : 'border-gray-300'}`}
                >
                  <option value={0}>Seleccionar agente...</option>
                  {agents.map(agent => (
                    <option key={agent.id} value={agent.id}>
                      {agent.hostname} ({agent.ip_address})
                    </option>
                  ))}
                </select>
                {formErrors.agent_id && (
                  <p className="text-red-500 text-xs mt-1">{formErrors.agent_id}</p>
                )}
              </div>
              
              {/* Configuración del túnel */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Host remoto
                  </label>
                  <input
                    type="text"
                    name="remote_host"
                    value={formData.remote_host}
                    onChange={handleFormChange}
                    placeholder="192.168.1.100"
                    className={`w-full p-2 border rounded-md ${formErrors.remote_host ? 'border-red-500' : 'border-gray-300'}`}
                  />
                  {formErrors.remote_host && (
                    <p className="text-red-500 text-xs mt-1">{formErrors.remote_host}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Puerto remoto
                  </label>
                  <input
                    type="number"
                    name="remote_port"
                    value={formData.remote_port}
                    onChange={handleFormChange}
                    placeholder="22"
                    className={`w-full p-2 border rounded-md ${formErrors.remote_port ? 'border-red-500' : 'border-gray-300'}`}
                  />
                  {formErrors.remote_port && (
                    <p className="text-red-500 text-xs mt-1">{formErrors.remote_port}</p>
                  )}
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Puerto local
                </label>
                <input
                  type="number"
                  name="local_port"
                  value={formData.local_port}
                  onChange={handleFormChange}
                  placeholder="8022"
                  className={`w-full p-2 border rounded-md ${formErrors.local_port ? 'border-red-500' : 'border-gray-300'}`}
                />
                {formErrors.local_port && (
                  <p className="text-red-500 text-xs mt-1">{formErrors.local_port}</p>
                )}
              </div>
              
              {/* Descripción */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción (opcional)
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleFormChange}
                  placeholder="Describe el propósito de este túnel"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  rows={2}
                />
              </div>
              
              {/* Credenciales SSH (opcional) */}
              <details className="mb-4">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
                  Configuración SSH avanzada (opcional)
                </summary>
                <div className="mt-3 pl-2 border-l-2 border-gray-200">
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Host SSH
                      </label>
                      <input
                        type="text"
                        name="ssh_host"
                        value={formData.ssh_host}
                        onChange={handleFormChange}
                        placeholder="jump-server.example.com"
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Puerto SSH
                      </label>
                      <input
                        type="number"
                        name="ssh_port"
                        value={formData.ssh_port}
                        onChange={handleFormChange}
                        placeholder="22"
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Usuario SSH
                      </label>
                      <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleFormChange}
                        placeholder="admin"
                        className={`w-full p-2 border rounded-md ${formErrors.username ? 'border-red-500' : 'border-gray-300'}`}
                      />
                      {formErrors.username && (
                        <p className="text-red-500 text-xs mt-1">{formErrors.username}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Contraseña SSH
                      </label>
                      <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleFormChange}
                        placeholder="**********"
                        className={`w-full p-2 border rounded-md ${formErrors.password ? 'border-red-500' : 'border-gray-300'}`}
                      />
                      {formErrors.password && (
                        <p className="text-red-500 text-xs mt-1">{formErrors.password}</p>
                      )}
                    </div>
                  </div>
                </div>
              </details>
              
              {/* Error general */}
              {formErrors.submit && (
                <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-500 text-sm">{formErrors.submit}</p>
                </div>
              )}
              
              {/* Botones */}
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors flex items-center"
                >
                  {createLoading ? (
                    <>
                      <Loader size={16} className="animate-spin mr-2" />
                      Creando...
                    </>
                  ) : (
                    'Crear túnel'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TunnelList;