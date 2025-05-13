import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axiosInstance from '../../lib/axios';
import { Button } from '@/components/ui/button';
import { Loader2, ArrowLeft } from 'lucide-react';
import { AlertTriangle } from 'lucide-react';

interface OID {
  id: number;
  name: string;
  oid: string;
  description: string;
  type: string;
}

const OIDEdit = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [oid, setOid] = useState('');
  const [type, setType] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOID = async () => {
      try {
        setLoading(true);
        const response = await axiosInstance.get(`/printer-oids/${id}`);
        const oidData = response.data;
        setName(oidData.name);
        setOid(oidData.oid);
        setType(oidData.type);
        setDescription(oidData.description || '');
        setError(null);
      } catch (err: any) {
        console.error('Error fetching OID:', err);
        setError(`Error al cargar el OID: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchOID();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !oid || !type) {
      setError('Por favor complete todos los campos obligatorios');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      
      await axiosInstance.put(`/printer-oids/${id}`, {
        name,
        oid,
        type,
        description
      });

      navigate('/printer-oids');
    } catch (err: any) {
      console.error('Error updating OID:', err);
      setError(`Error al actualizar el OID: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center mb-6">
        <Button 
          variant="outline" 
          onClick={() => navigate('/printer-oids')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <h1 className="text-2xl font-bold">Editar OID</h1>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg mb-6 flex items-center">
          <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="bg-white shadow-md rounded-lg p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="name">
              Nombre *
            </label>
            <input
              id="name"
              type="text"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="oid">
              OID *
            </label>
            <input
              id="oid"
              type="text"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={oid}
              onChange={(e) => setOid(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="type">
              Tipo *
            </label>
            <select
              id="type"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={type}
              onChange={(e) => setType(e.target.value)}
              required
            >
              <option value="">Seleccionar tipo</option>
              <option value="string">String</option>
              <option value="integer">Integer</option>
              <option value="gauge">Gauge</option>
              <option value="counter">Counter</option>
              <option value="timeticks">Timeticks</option>
              <option value="ipaddress">IP Address</option>
              <option value="objectid">Object ID</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="description">
              Descripción
            </label>
            <textarea
              id="description"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
            />
          </div>

          <div className="flex justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/printer-oids')}
              className="mr-2"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={saving}
            >
              {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Guardar Cambios
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default OIDEdit;