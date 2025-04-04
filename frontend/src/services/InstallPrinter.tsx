// src/components/printers/InstallPrinter.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PrinterService } from '../../services/PrinterService';
import { DriverService, Driver } from '../../services/DriverService';
import { AgentService, Agent } from '../../services/AgentService';
import { Printer, Terminal, Server, ChevronLeft, Loader, AlertCircle, CheckCircle } from 'lucide-react';

interface InstallPrinterFormData {
  printer_ip: string;
  driver_id: number;
}

const InstallPrinter = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [installLoading, setInstallLoading] = useState(false);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [formData, setFormData] = useState<InstallPrinterFormData>({
    printer_ip: '',
    driver_id: 0
  });
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [installSuccess, setInstallSuccess] = useState(false);
  const [installMessage, setInstallMessage] = useState('');
  const [installError, setInstallError] = useState('');

  // Cargar datos iniciales
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Cargar datos del agente
        if (agentId) {
          const agentData = await AgentService.getAgentById(parseInt(agentId));
          setAgent(agentData);
        }
        
        // Cargar drivers disponibles
        const driversData = await DriverService.getDrivers();
        setDrivers(driversData);
      } catch (error) {
        console.error('Error cargando datos iniciales', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [agentId]);

  // Manejar cambios en el formulario
  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'driver_id' ? parseInt(value) : value
    });
  };

  // Validar formulario
  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    
    const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
    
    if (!formData.printer_ip) {
      errors.printer_ip = 'Ingresa la dirección IP de la impresora';
    } else if (!ipRegex.test(formData.printer_ip)) {
      errors.printer_ip = 'Ingresa una dirección IP válida (formato: 192.168.1.100)';
    }
    
    if (!formData.driver_id) {
      errors.driver_id = 'Selecciona un controlador para la impresora';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Enviar solicitud de instalación
  const handleInstall = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      setInstallLoading(true);
      setInstallSuccess(false);
      setInstallMessage('');
      setInstallError('');
      
      // Asegurarse de que el agentId existe
      if (!agentId) {
        throw new Error('ID de agente no proporcionado');
      }
      
      const response = await PrinterService.installPrinter(
        agent?.token || '', // Usando token del agente en lugar del ID
        formData
      );
      
      setInstallSuccess(true);
      setInstallMessage(response.message || 'Comando de instalación enviado correctamente al agente.');
      
      // Limpiar formulario después de una instalación exitosa
      setFormData({
        printer_ip: '',
        driver_id: 0
      });
      
    } catch (error: any) {
      console.error('Error instalando impresora', error);
      setInstallError(
        error.response?.data?.detail || 
        'Ocurrió un error al intentar instalar la impresora. Verifica que el agente esté conectado.'
      );
    } finally {
      setInstallLoading(false);
    }
  };

  // Estado de carga
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-pulse text-gray-400">Cargando...</div>
      </div>
    );
  }

  // Si no se encuentra el agente
  if (!agent) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertCircle size={20} className="text-red-500 mr-2" />
            <h2 className="text-red-600 font-medium">Agente no encontrado</h2>
          </div>
          <p className="mt-2 text-red-600">
            No se pudo encontrar el agente con ID {agentId}. Por favor, verifica que el agente exista e intenta nuevamente.
          </p>
          <button
            onClick={() => navigate('/agents')}
            className="mt-3 flex items-center text-red-600 hover:text-red-800"
          >
            <ChevronLeft size={16} />
            <span>Volver a la lista de agentes</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <button
          onClick={() => navigate(`/agents/${agentId}`)}
          className="flex items-center text-gray-600 hover:text-blue-600 mb-2"
        >
          <ChevronLeft size={16} />
          <span>Volver al agente</span>
        </button>
        <h1 className="text-2xl font-light text-gray-800">Instalar impresora</h1>
        <p className="text-gray-600">
          Envía un comando de instalación de impresora al agente <strong>{agent.hostname}</strong>
        </p>
      </div>

      {/* Información del agente */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-800 mb-4">Información del agente</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Hostname</p>
            <p className="font-medium">{agent.hostname}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Dirección IP</p>
            <p className="font-medium">{agent.ip_address}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Tipo de dispositivo</p>
            <div className="flex items-center">
              {agent.device_type === 'server' ? (
                <Server size={16} className="text-gray-500 mr-1" />
              ) : (
                <Terminal size={16} className="text-gray-500 mr-1" />
              )}
              <span>{agent.device_type}</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500">Estado</p>
            <p className={`font-medium ${
              agent.status === 'active' ? 'text-green-600' : 'text-red-600'
            }`}>
              {agent.status === 'active' ? 'Activo' : 'Inactivo'}
            </p>
          </div>
        </div>
      </div>

      {/* Mensajes de feedback */}
      {installSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <CheckCircle size={20} className="text-green-500 mr-2" />
            <h2 className="text-green-600 font-medium">Comando enviado correctamente</h2>
          </div>
          <p className="mt-2 text-green-600">
            {installMessage}
          </p>
        </div>
      )}

      {installError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertCircle size={20} className="text-red-500 mr-2" />
            <h2 className="text-red-600 font-medium">Error al enviar el comando</h2>
          </div>
          <p className="mt-2 text-red-600">
            {installError}
          </p>
        </div>
      )}

      {/* Formulario de instalación */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-medium text-gray-800 mb-4">Configuración de la impresora</h2>
        
        <form onSubmit={handleInstall}>
          {/* Dirección IP de la impresora */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dirección IP de la impresora
            </label>
            <input
              type="text"
              name="printer_ip"
              value={formData.printer_ip}
              onChange={handleFormChange}
              placeholder="192.168.1.100"
              className={`w-full p-2 border rounded-md ${
                formErrors.printer_ip ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {formErrors.printer_ip && (
              <p className="text-red-500 text-xs mt-1">{formErrors.printer_ip}</p>
            )}
          </div>
          
          {/* Selección de driver */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Controlador de impresora
            </label>
            <select
              name="driver_id"
              value={formData.driver_id}
              onChange={handleFormChange}
              className={`w-full p-2 border rounded-md ${
                formErrors.driver_id ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value={0}>Seleccionar controlador...</option>
              {drivers.map(driver => (
                <option key={driver.id} value={driver.id}>
                  {driver.manufacturer} {driver.model}
                </option>
              ))}
            </select>
            {formErrors.driver_id && (
              <p className="text-red-500 text-xs mt-1">{formErrors.driver_id}</p>
            )}
          </div>
          
          {/* Botón de instalación */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={installLoading || agent.status !== 'active'}
              className={`px-4 py-2 rounded-md flex items-center ${
                agent.status !== 'active'
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              {installLoading ? (
                <>
                  <Loader size={16} className="animate-spin mr-2" />
                  <span>Enviando comando...</span>
                </>
              ) : (
                <>
                  <Printer size={16} className="mr-2" />
                  <span>Instalar impresora</span>
                </>
              )}
            </button>
          </div>
          
          {agent.status !== 'active' && (
            <p className="text-amber-600 text-sm mt-2">
              El agente debe estar activo para poder instalar impresoras. Verifica la conexión del agente.
            </p>
          )}
        </form>
      </div>
    </div>
  );
};

export default InstallPrinter;