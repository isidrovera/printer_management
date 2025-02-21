import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
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
    console.log('Iniciando proceso de login para usuario:', formData.username);
    setError('');
    setLoading(true);

    try {
      const formDataObj = new FormData();
      formDataObj.append('username', formData.username);
      formDataObj.append('password', formData.password);

      console.log('Enviando petición de login al servidor');
      const response = await axios.post('/api/auth/login', formDataObj);
      
      console.log('Respuesta del servidor recibida:', { 
        status: response.status,
        user: response.data.user.username 
      });

      login(response.data.access_token, response.data.user);

      // Redireccionar según el estado del usuario
      if (response.data.user.must_change_password) {
        console.log('Usuario debe cambiar contraseña, redirigiendo...');
        navigate('/change-password');
      } else {
        console.log('Login exitoso, redirigiendo al dashboard...');
        navigate('/dashboard');
      }
      
    } catch (err: any) {
      console.error('Error de login:', err);
      console.error('Detalles del error:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Iniciar Sesión
        </h2>
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
                onChange={(e) => {
                  console.log('Campo username actualizado');
                  setFormData({...formData, username: e.target.value});
                }}
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
                onChange={(e) => {
                  console.log('Campo password actualizado');
                  setFormData({...formData, password: e.target.value});
                }}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default Login;