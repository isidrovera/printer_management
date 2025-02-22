import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Alert } from '../../components/ui/alert';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('Iniciando login con:', {
        username: formData.username,
        password: '********'
      });
      
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: formData.username,
          password: formData.password
        }),
        credentials: 'include'
      });

      console.log('Status:', response.status);
      const contentType = response.headers.get("content-type");
      console.log('Content-Type:', contentType);

      if (!response.ok) {
        const errorData = contentType?.includes('application/json') 
          ? await response.json()
          : await response.text();
        console.error('Error response:', errorData);
        throw new Error(typeof errorData === 'object' ? errorData.detail : 'Error al iniciar sesión');
      }

      const data = await response.json();
      console.log('Login exitoso:', data);

      // Guardar el token y datos del usuario
      login(data.access_token, data.user);

      // Redireccionar según el estado del usuario
      if (data.user.must_change_password) {
        navigate('/change-password');
      } else {
        navigate('/dashboard');
      }

    } catch (err) {
      console.error('Error completo:', err);
      setError(err instanceof Error ? err.message : 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            Sistema de Monitoreo de Impresoras Inteligente
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Gestiona, monitorea y optimiza tu flota de impresoras desde una única plataforma centralizada
          </p>
        </div>
      </div>

      {/* Login Form */}
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <h2 className="mb-6 text-center text-2xl font-bold text-gray-900">
            Iniciar Sesión
          </h2>

          {error && (
            <Alert className="mb-6" variant="destructive">
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Usuario
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Contraseña
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700"
              disabled={loading}
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>
          </form>
        </Card>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-white">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-2">Monitoreo en Tiempo Real</h3>
              <p className="text-gray-600">
                Supervisa el estado de tus impresoras en tiempo real, niveles de tinta y estado operativo
              </p>
            </div>
          </Card>

          <Card className="bg-white">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-2">Gestión de Firmware</h3>
              <p className="text-gray-600">
                Descarga y actualiza firmware fácilmente con nuestro sistema centralizado
              </p>
            </div>
          </Card>

          <Card className="bg-white">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-2">Comunidad Activa</h3>
              <p className="text-gray-600">
                Participa en nuestro foro y comparte experiencias con otros usuarios
              </p>
            </div>
          </Card>

          <Card className="bg-white">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-2">Documentación Completa</h3>
              <p className="text-gray-600">
                Accede a manuales detallados y guías de solución de problemas
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Login;