// src/components/printers/PrinterList.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PrinterService, Printer } from '../../services/PrinterService';
import { Eye, Edit, Trash2, Plus, Search, X, Printer as PrinterIcon } from 'lucide-react';

const PrinterList = () => {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPrinter, setSelectedPrinter] = useState<Printer | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    loadPrinters();
  }, [searchTerm]);

  const loadPrinters = async () => {
    try {
      setLoading(true);
      const data = await PrinterService.getPrinters();
      setPrinters(data);
    } catch (error) {
      console.error('Error al cargar las impresoras', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedPrinter?.id) return;
    try {
      await PrinterService.deletePrinter(selectedPrinter.id);
      setPrinters(printers.filter(p => p.id !== selectedPrinter.id));
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Error al eliminar la impresora', error);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800';
      case 'offline':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
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
        <h1 className="text-2xl font-light text-gray-800">Impresoras</h1>
        <Link 
          to="/printers/create" 
          className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-full transition-colors shadow-sm flex items-center"
          title="Nueva Impresora"
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
          placeholder="Buscar impresoras..."
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

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Total Impresoras</h3>
          <p className="text-2xl font-bold">{printers.length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Online</h3>
          <p className="text-2xl font-bold text-green-600">
            {printers.filter(p => p.status === 'online').length}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Offline</h3>
          <p className="text-2xl font-bold text-gray-600">
            {printers.filter(p => p.status === 'offline').length}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Error</h3>
          <p className="text-2xl font-bold text-red-600">
            {printers.filter(p => p.status === 'error').length}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">IP</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Marca/Modelo</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-4 text-left font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
              <th className="px-6 py-4 text-right font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {printers.length === 0 ? (
              <tr key="no-printers-row">
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  No se encontraron impresoras
                </td>
              </tr>
            ) : (
              printers.map((printer, index) => (
                <tr key={printer.id || `printer-${index}`} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">{printer.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{printer.ip_address}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{printer.brand} {printer.model}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClass(printer.status)}`}>
                      {printer.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {printer.client_id ? `Cliente ${printer.client_id}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex justify-end gap-2">
                      <Link 
                        to={`/printers/${printer.id}`}
                        className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                        title="Ver detalles"
                      >
                        <Eye size={18} />
                      </Link>
                      <Link 
                        to={`/printers/${printer.id}/edit`}
                        className="p-1 text-gray-400 hover:text-green-500 transition-colors"
                        title="Editar impresora"
                      >
                        <Edit size={18} />
                      </Link>
                      <button
                        onClick={() => {
                          setSelectedPrinter(printer);
                          setShowDeleteModal(true);
                        }}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        title="Eliminar impresora"
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
            <h2 className="text-xl font-medium mb-3">¿Eliminar impresora?</h2>
            <p className="mb-4 text-gray-600">
              ¿Estás seguro de eliminar la impresora <span className="font-medium">{selectedPrinter?.name}</span>? Esta acción no se puede deshacer.
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

export default PrinterList;