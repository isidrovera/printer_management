import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../../lib/axios';
import { Button } from '@/components/ui/button';
import { Loader2, ArrowLeft, Upload } from 'lucide-react';
import { AlertTriangle } from 'lucide-react';

const DriverCreate = () => {
  const navigate = useNavigate();
  const [manufacturer, setManufacturer] = useState('');
  const [model, setModel] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!manufacturer || !model || !file) {
      setError('Por favor complete todos los campos obligatorios');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('manufacturer', manufacturer);
      formData.append('model', model);
      formData.append('description', description);
      formData.append('driver_file', file);

      await axiosInstance.post('/drivers', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      navigate('/drivers');
    } catch (err: any) {
      console.error('Error creating driver:', err);
      setError(`Error al crear el driver: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center mb-6">
        <Button 
          variant="outline" 
          onClick={() => navigate('/drivers')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <h1 className="text-2xl font-bold">Agregar Nuevo Driver</h1>
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
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="manufacturer">
              Fabricante *
            </label>
            <input
              id="manufacturer"
              type="text"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={manufacturer}
              onChange={(e) => setManufacturer(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="model">
              Modelo *
            </label>
            <input
              id="model"
              type="text"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
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

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="driver_file">
              Archivo del Driver *
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
              <div className="space-y-1 text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label
                    htmlFor="driver_file"
                    className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none"
                  >
                    <span>Seleccione un archivo</span>
                    <input
                      id="driver_file"
                      name="driver_file"
                      type="file"
                      className="sr-only"
                      onChange={handleFileChange}
                      required
                    />
                  </label>
                  <p className="pl-1">o arrastre aquí</p>
                </div>
                <p className="text-xs text-gray-500">ZIP, RAR, o otros formatos de archivo de driver</p>
                {file && (
                  <p className="text-sm text-green-600">
                    Archivo seleccionado: {file.name}
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/drivers')}
              className="mr-2"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={loading}
            >
              {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Guardar
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DriverCreate;