import React, { useState, useEffect } from 'react';
import axiosInstance from '../../lib/axios';
import { 
  AlertTriangle, 
  Plus, 
  Edit, 
  Trash2, 
  Search,
  Loader2,
  Settings
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface OID {
  id: number;
  name: string;
  oid: string;
  description: string;
  type: string;
}

const OIDList = () => {
  const [oids, setOIDs] = useState<OID[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchOIDs = async () => {
      try {
        setLoading(true);
        const response = await axiosInstance.get('/printer-oids');
        setOIDs(response.data);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching OIDs:', err);
        setError(`Error al cargar los OIDs: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchOIDs();
  }, []);

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Estás seguro de que deseas eliminar este OID?')) {
      try {
        await axiosInstance.delete(`/printer-oids/${id}`);
        setOIDs(oids.filter(oid => oid.id !== id));
      } catch (err: any) {
        console.error('Error deleting OID:', err);
        setError(`Error al eliminar el OID: ${err.message}`);
      }
    }
  };

  const filteredOIDs = oids.filter(oid =>
    oid.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    oid.oid.toLowerCase().includes(searchTerm.toLowerCase()) ||
    oid.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    oid.type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Gestión de OIDs de Impresoras</h1>
        <Button 
          onClick={() => navigate('/printer-oids/create')} 
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Nuevo OID
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg mb-6 flex items-center">
          <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="mb-6">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Buscar por nombre, OID, tipo o descripción..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {filteredOIDs.length === 0 ? (
        <div className="text-center py-10 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No se encontraron OIDs</p>
        </div>
      ) : (
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredOIDs.map((oid) => (
                <tr key={oid.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{oid.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{oid.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{oid.oid}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{oid.type}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{oid.description}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/printer-oids/${oid.id}/edit`)}
                        className="flex items-center"
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        Editar
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(oid.id)}
                        className="flex items-center text-red-500 hover:text-red-600 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Eliminar
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default OIDList;