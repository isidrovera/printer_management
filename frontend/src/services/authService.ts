// src/services/authService.ts
import axios from 'axios';

const API_URL = 'http://161.132.39.159:8000/api/v1';

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
});

export const authService = {
  login: async (username: string, password: string) => {
    try {
      // Usamos /auth/token en lugar de /auth/login
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('grant_type', 'password'); // Requerido por OAuth2PasswordRequestForm

      const response = await axiosInstance.post('/auth/token', formData);
      
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        axiosInstance.defaults.headers.common['Authorization'] = 
          `Bearer ${response.data.access_token}`;
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error en login:', error);
      if (error.response?.status === 401) {
        throw new Error('Credenciales incorrectas');
      }
      throw new Error(error.response?.data?.detail || 'Error en la autenticación');
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    delete axiosInstance.defaults.headers.common['Authorization'];
  },

  // Verificar si el usuario está autenticado
  isAuthenticated: () => {
    const token = localStorage.getItem('token');
    return !!token;
  }
};

export default authService;