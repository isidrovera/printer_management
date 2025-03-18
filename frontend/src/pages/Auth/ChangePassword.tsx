// src/pages/Auth/ChangePassword.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Alert } from '../../components/ui/alert';
import axiosInstance from '../../lib/axios';  // <-- asegúrate que sea esta ruta exacta

const ChangePassword = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    console.log('🔄 Formulario enviado', formData);

    if (formData.newPassword !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden');
      console.error('❌ Error: Las contraseñas no coinciden');
      return;
    }

    setLoading(true);
    console.log('🔄 Iniciando petición al backend para cambiar contraseña');

    try {
      const response = await axiosInstance.post('/auth/change-password', {
        current_password: formData.currentPassword,
        new_password: formData.newPassword,
      });

      console.log('✅ Respuesta exitosa del backend:', response.data);

      navigate('/');
      console.log('🚀 Usuario redirigido a página principal');
    } catch (err: any) {
      console.error('❌ Error al cambiar contraseña:', err.response?.data);
      setError(err.response?.data?.detail || 'Error al cambiar la contraseña');
    } finally {
      setLoading(false);
      console.log('🔄 Fin del proceso de cambio de contraseña');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Cambiar Contraseña
        </h2>
        {user?.must_change_password && (
          <p className="mt-2 text-center text-sm text-gray-600">
            Debes cambiar tu contraseña antes de continuar
          </p>
        )}
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {error && (
            <Alert className="mb-6" variant="destructive">
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700">
                Contraseña Actual
              </label>
              <input
                id="currentPassword"
                type="password"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                value={formData.currentPassword}
                onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
              />
            </div>

            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                Nueva Contraseña
              </label>
              <input
                id="newPassword"
                type="password"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                value={formData.newPassword}
                onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirmar Nueva Contraseña
              </label>
              <input
                id="confirmPassword"
                type="password"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Cambiando contraseña...' : 'Cambiar Contraseña'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default ChangePassword;
