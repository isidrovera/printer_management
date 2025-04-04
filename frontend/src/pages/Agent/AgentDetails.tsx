import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { AgentService, Agent } from '../../services/AgentService';
import { 
  ArrowLeft, Edit, Trash2, Laptop, Server, Monitor, Clipboard, 
  Check, AlertCircle, HardDrive, Cpu, Wifi, Battery, 
  Database, Globe, User, MapPin, Info
} from 'lucide-react';

const AgentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

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
        return <Monitor size={24} className="text-blue-500" />;
      case 'server':
        return <Server size={24} className="text-purple-500" />;
      case 'windows':
        return <Monitor size={24} className="text-blue-500" />;
      default:
        return <Laptop size={24} className="text-indigo-500" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'online':
        return <Check size={16} className="text-green-500" />;
      case 'inactive':
      case 'offline':
        return <AlertCircle size={16} className="text-red-500" />;
      default:
        return <AlertCircle size={16} className="text-amber-500" />;
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'active':
      case 'online':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'inactive':
      case 'offline':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-amber-100 text-amber-800 border-amber-200';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-pulse flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
            <Laptop className="text-blue-500 animate-pulse" />
          </div>
          <div className="text-gray-600">Cargando información del agente...</div>
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="mb-6">
          <Link to="/agents" className="text-blue-500 hover:underline flex items-center">
            <ArrowLeft size={18} className="mr-1" /> Volver a la lista
          </Link>
        </div>
        <div className="bg-white p-8 rounded-lg shadow-md text-center">
          <AlertCircle size={48} className="mx-auto text-amber-500 mb-4" />
          <h2 className="text-xl font-medium mb-4">Agente no encontrado</h2>
          <p className="text-gray-600 mb-6">El agente que estás buscando no existe o ha sido eliminado.</p>
          <Link to="/agents" className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors">
            Volver a agentes
          </Link>
        </div>
      </div>
    );
  }

  const systemInfo = agent.system_info || {};

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6 flex justify-between items-center">
        <Link to="/agents" className="text-blue-500 hover:underline flex items-center group">
          <ArrowLeft size={18} className="mr-1 group-hover:translate-x-[-2px] transition-transform" /> Volver a la lista
        </Link>
        <div className="flex space-x-2">
          <Link 
            to={`/agents/${agent.id}/edit`}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors flex items-center shadow-sm"
          >
            <Edit size={18} className="mr-1" /> Editar
          </Link>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md transition-colors flex items-center shadow-sm"
          >
            <Trash2 size={18} className="mr-1" /> Eliminar
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Header Card */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
            <div className="flex items-center">
              <div className="rounded-lg bg-white/20 backdrop-blur-sm p-3 mr-4">
                {getDeviceIcon(agent.device_type)}
              </div>
              <div>
                <h1 className="text-2xl font-medium">{agent.hostname}</h1>
                <div className="flex items-center mt-1">
                  <div className={`px-3 py-1 text-sm font-medium rounded-full border ${getStatusClass(agent.status)} flex items-center gap-1.5`}>
                    {getStatusIcon(agent.status)}
                    {agent.status === 'active' ? 'Activo' : 
                     agent.status === 'inactive' ? 'Inactivo' : agent.status}
                  </div>
                  <span className="mx-2 text-white/70">•</span>
                  <span className="text-sm">{agent.ip_address}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="p-4 border-b flex items-center">
            <div className="flex items-center border rounded-lg overflow-hidden flex-grow">
              <div className="py-2 px-3 bg-gray-50 text-gray-500 text-sm font-medium">TOKEN</div>
              <code className="py-2 px-3 text-sm font-mono break-all flex-grow">{agent.token}</code>
              <button 
                onClick={copyToClipboard}
                className="p-2 text-gray-400 hover:text-blue-500 transition-colors border-l bg-white"
                title="Copiar token"
              >
                <Clipboard size={18} />
              </button>
            </div>
            {copiedToken && (
              <span className="ml-2 text-xs text-green-600 flex items-center">
                <Check size={16} className="mr-1" /> ¡Copiado!
              </span>
            )}
          </div>

          {/* Tabs navigation */}
          <div className="border-b">
            <nav className="flex overflow-x-auto">
              <button 
                onClick={() => setActiveTab('overview')}
                className={`px-4 py-3 text-sm font-medium whitespace-nowrap flex items-center border-b-2 ${
                  activeTab === 'overview' 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Info size={16} className="mr-1.5" /> Información general
              </button>
              <button 
                onClick={() => setActiveTab('hardware')}
                className={`px-4 py-3 text-sm font-medium whitespace-nowrap flex items-center border-b-2 ${
                  activeTab === 'hardware' 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Cpu size={16} className="mr-1.5" /> Hardware
              </button>
              <button 
                onClick={() => setActiveTab('storage')}
                className={`px-4 py-3 text-sm font-medium whitespace-nowrap flex items-center border-b-2 ${
                  activeTab === 'storage' 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <HardDrive size={16} className="mr-1.5" /> Almacenamiento
              </button>
              <button 
                onClick={() => setActiveTab('network')}
                className={`px-4 py-3 text-sm font-medium whitespace-nowrap flex items-center border-b-2 ${
                  activeTab === 'network' 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Wifi size={16} className="mr-1.5" /> Red
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-gray-50 rounded-lg p-4 flex items-start">
                  <div className="bg-blue-100 p-2 rounded-lg mr-3">
                    <User size={20} className="text-blue-600" />
                  </div>
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1">Usuario</div>
                    <div className="font-medium">{agent.username}</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4 flex items-start">
                  <div className="bg-violet-100 p-2 rounded-lg mr-3">
                    <Monitor size={20} className="text-violet-600" />
                  </div>
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1">Tipo de dispositivo</div>
                    <div className="font-medium">{agent.device_type}</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4 flex items-start">
                  <div className="bg-green-100 p-2 rounded-lg mr-3">
                    <Globe size={20} className="text-green-600" />
                  </div>
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1">Sistema operativo</div>
                    <div className="font-medium">
                      {systemInfo?.Sistema?.['Nombre del SO']} {systemInfo?.Sistema?.['Versión del SO']}
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4 flex items-start">
                  <div className="bg-amber-100 p-2 rounded-lg mr-3">
                    <MapPin size={20} className="text-amber-600" />
                  </div>
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1">Dirección IP</div>
                    <div className="font-medium">{agent.ip_address}</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4 flex items-start">
                  <div className="bg-red-100 p-2 rounded-lg mr-3">
                    <Cpu size={20} className="text-red-600" />
                  </div>
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1">Procesador</div>
                    <div className="font-medium text-sm">
                      {systemInfo?.CPU?.Modelo?.split(',')[0]}
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4 flex items-start">
                  <div className="bg-indigo-100 p-2 rounded-lg mr-3">
                    <Battery size={20} className="text-indigo-600" />
                  </div>
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1">Batería</div>
                    <div className="font-medium">
                      {systemInfo?.Batería ? `${systemInfo.Batería.Porcentaje}% ${systemInfo.Batería.Enchufado ? '(Cargando)' : ''}` : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Hardware Tab */}
            {activeTab === 'hardware' && systemInfo?.CPU && systemInfo?.Memoria && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* CPU Card */}
                <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
                  <div className="bg-blue-50 px-4 py-3 border-b">
                    <div className="flex items-center">
                      <Cpu size={20} className="text-blue-600 mr-2" />
                      <h3 className="font-medium">Procesador</h3>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 text-sm">
                        <div className="text-gray-500">Modelo</div>
                        <div className="font-medium">{systemInfo.CPU.Modelo || 'N/A'}</div>
                      </div>
                      <div className="grid grid-cols-2 text-sm">
                        <div className="text-gray-500">Núcleos físicos</div>
                        <div className="font-medium">{systemInfo.CPU['Núcleos físicos'] || 'N/A'}</div>
                      </div>
                      <div className="grid grid-cols-2 text-sm">
                        <div className="text-gray-500">Núcleos lógicos</div>
                        <div className="font-medium">{systemInfo.CPU['Núcleos lógicos'] || 'N/A'}</div>
                      </div>
                      <div className="grid grid-cols-2 text-sm">
                        <div className="text-gray-500">Frecuencia</div>
                        <div className="font-medium">{systemInfo.CPU['Frecuencia (MHz)'] ? `${systemInfo.CPU['Frecuencia (MHz)']} MHz` : 'N/A'}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-sm mb-1">Uso actual</div>
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div 
                            className="bg-blue-600 h-2.5 rounded-full" 
                            style={{ width: `${systemInfo.CPU['Uso actual (%)'] || 0}%` }}
                          ></div>
                        </div>
                        <div className="text-xs font-medium text-gray-500 mt-1 text-right">{systemInfo.CPU['Uso actual (%)'] || 0}%</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Memory Card */}
                <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
                  <div className="bg-green-50 px-4 py-3 border-b">
                    <div className="flex items-center">
                      <HardDrive size={20} className="text-green-600 mr-2" />
                      <h3 className="font-medium">Memoria</h3>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 text-sm">
                        <div className="text-gray-500">RAM Total</div>
                        <div className="font-medium">{systemInfo.Memoria['Total RAM (GB)'] ? `${systemInfo.Memoria['Total RAM (GB)']} GB` : 'N/A'}</div>
                      </div>
                      <div className="grid grid-cols-2 text-sm">
                        <div className="text-gray-500">RAM Disponible</div>
                        <div className="font-medium">{systemInfo.Memoria['Disponible RAM (GB)'] ? `${systemInfo.Memoria['Disponible RAM (GB)']} GB` : 'N/A'}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-sm mb-1">Uso de RAM</div>
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div 
                            className="bg-green-600 h-2.5 rounded-full" 
                            style={{ width: `${systemInfo.Memoria['Uso de RAM (%)'] || 0}%` }}
                          ></div>
                        </div>
                        <div className="text-xs font-medium text-gray-500 mt-1 text-right">{systemInfo.Memoria['Uso de RAM (%)'] || 0}%</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Storage Tab */}
            {activeTab === 'storage' && systemInfo?.Discos && (
              <div className="space-y-6">
                {systemInfo.Discos.map((disk, index) => (
                  <div key={index} className="bg-white border rounded-lg overflow-hidden shadow-sm">
                    <div className="bg-purple-50 px-4 py-3 border-b">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <Database size={20} className="text-purple-600 mr-2" />
                          <h3 className="font-medium">Disco {disk['Dispositivo']}</h3>
                        </div>
                        <div className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                          {disk['Tipo de sistema de archivos']}
                        </div>
                      </div>
                    </div>
                    <div className="p-4">
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-500">Espacio usado</span>
                            <span className="font-medium">{disk['Usado (GB)']} GB de {disk['Total (GB)']} GB</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2.5">
                            <div 
                              className="bg-purple-600 h-2.5 rounded-full" 
                              style={{ width: `${disk['Porcentaje de uso (%)']}%` }}
                            ></div>
                          </div>
                          <div className="text-xs font-medium text-gray-500 mt-1 text-right">{disk['Porcentaje de uso (%)']}%</div>
                        </div>
                        <div className="grid grid-cols-2 text-sm">
                          <div className="text-gray-500">Disponible</div>
                          <div className="font-medium">{disk['Disponible (GB)']} GB</div>
                        </div>
                        <div className="grid grid-cols-2 text-sm">
                          <div className="text-gray-500">Punto de montaje</div>
                          <div className="font-medium">{disk['Punto de montaje']}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Network Tab */}
            {activeTab === 'network' && systemInfo?.Red && (
              <div className="space-y-6">
                {Object.entries(systemInfo.Red).map(([interfaceName, details], idx) => (
                  <div key={idx} className="bg-white border rounded-lg overflow-hidden shadow-sm">
                    <div className="bg-blue-50 px-4 py-3 border-b">
                      <div className="flex items-center">
                        <Wifi size={20} className="text-blue-600 mr-2" />
                        <h3 className="font-medium">{interfaceName}</h3>
                      </div>
                    </div>
                    <div className="p-4">
                      <div className="space-y-4">
                        {Array.isArray(details) && details.map((detail, index) => (
                          <div key={index} className="grid grid-cols-2 text-sm">
                            <div className="text-gray-500">{detail.Tipo}</div>
                            <div className="font-medium">{detail.Dirección || 'N/A'}</div>
                            {detail['Máscara de red'] && (
                              <>
                                <div className="text-gray-500 col-start-1 mt-1">Máscara</div>
                                <div className="font-medium mt-1">{detail['Máscara de red']}</div>
                              </>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal de eliminación */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <div className="text-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 text-red-500 mb-4">
                <Trash2 size={24} />
              </div>
              <h2 className="text-xl font-medium">¿Eliminar agente?</h2>
            </div>
            <p className="mb-6 text-gray-600 text-center">
              ¿Estás seguro de eliminar el agente <span className="font-medium">{agent.hostname}</span>? Esta acción no se puede deshacer.
            </p>
            <div className="flex justify-center gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors flex-1"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md transition-colors flex-1"
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