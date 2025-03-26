// src/components/printers/PrinterForm.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { PrinterService, Printer } from '../../services/PrinterService';
import { ArrowLeft, Save, Trash2, AlertTriangle, Printer as PrinterIcon } from 'lucide-react';

interface FormProps {
  isEdit?: boolean;
}

const PrinterForm: React.FC<FormProps> = ({ isEdit = false }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  
  const [formData, setFormData] = useState<Printer>({
    name: '',
    brand: '',
    model: '',
    ip_address: '',
    status: 'offline',
    client_id: undefined
  });

  useEffect(() => {
    if (isEdit && id) {
      loadPrinter(parseInt(id));
    }
  }, [isEdit, id]);

  const loadPrinter = async (printerId: number) => {
    try {
      setLoading(true);
      const printerData = await PrinterService.getPrinterById(printerId);
      if (printerData) {
        setFormData(printerData);
      } else {
        setError('No se encontró la impresora');
        setTimeout(() => navigate('/printers'), 3000);
      }
    } catch (err) {
      setError('Error al cargar la información de la impresora');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    // Handle client_id special case to convert empty string to undefined
    if (name === 'client_id') {
      setFormData({
        ...formData,
        [name]: value === '' ? undefined : parseInt(value)
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      
      // Validate form data
      if (!formData.name || !formData.ip_address || !formData.brand || !formData.model) {
        setError('Por favor complete todos los campos obligatorios');
        setSaving(false);
        return;
      }
      
      if (isEdit && id) {
        await PrinterService.updatePrinter(parseInt(id), formData);
      } else {
        await PrinterService.createPrinter(formData);
      }
      
      navigate('/printers');
    } catch (err) {
      setError('Error al guardar la impresora');
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    
    try {
      await PrinterService.deletePrinter(parseInt(id));
      navigate('/printers');
    } catch (err) {
      setError('Error al eliminar la impresora');
      setShowDeleteModal(false);
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
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <Link to="/printers" className="inline-flex items-center text-blue-500 hover:text-blue-600 transition-colors">
          <ArrowLeft size={16} className="mr-1" />
          Volver a Impresoras
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-medium text-gray-800">
            {isEdit ? 'Editar Impresora' : 'Nueva Impresora'}
          </h1>
          {isEdit && (
            <button
              type="button"
              onClick={() => setShowDeleteModal(true)}
              className="text-red-500 hover:text-red-600 transition-colors"
              title="Eliminar impresora"
            >
              <Trash2 size={20} />
            </button>
          )}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md flex items-center">
            <AlertTriangle size={18} className="mr-2 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label htmlFor="ip_address" className="block text-sm font-medium text-gray-700 mb-1">
                  Dirección IP <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="ip_address"
                  name="ip_address"
                  value={formData.ip_address}
                  onChange={handleChange}
                  required
                  pattern="^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                  title="Ingrese una dirección IP válida (ej. 192.168.1.1)"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="brand" className="block text-sm font-medium text-gray-700 mb-1">
                  Marca <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="brand"
                  name="brand"
                  value={formData.brand}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label htmlFor="model" className="block text-sm font-medium text-gray-700 mb-1">
                  Modelo <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="model"
                  name="model"
                  value={formData.model}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                  Estado
                </label>
                <select
                  id="status"
                  name="status"
                  value={formData.status || 'offline'}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                  <option value="error">Error</option>
                </select>
              </div>
              <div>
                <label htmlFor="client_id" className="block text-sm font-medium text-gray-700 mb-1">
                  Cliente ID
                </label>
                <input
                  type="number"
                  id="client_id"
                  name="client_id"
                  value={formData.client_id || ''}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="mt-8 flex justify-end">
              <button
                type="button"
                onClick={() => navigate('/printers')}
                className="mr-4 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors flex items-center"
              >
                {saving ? (
                  <>
                    <span className="animate-spin inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></span>
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save size={18} className="mr-2" />
                    Guardar
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Modal de confirmación para eliminar */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h2 className="text-xl font-medium mb-3">¿Eliminar impresora?</h2>
            <p className="mb-4 text-gray-600">
              ¿Estás seguro de eliminar la impresora <span className="font-medium">{formData.name}</span>? Esta acción no se puede deshacer.
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

export default PrinterForm;