// src/services/authService.ts
import axios from 'axios';

const API_URL = 'http://161.132.39.159:8000/api/v1';

const axiosInstance = axios.create({
  baseURL: API_URL,
  withCredentials: true,  // Importante para CORS
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
});

export const authService = {
  login: async (username: string, password: string) => {
    try {
      // Usar la ruta de login directamente en lugar de /token
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axiosInstance.post('/auth/login', formData);
      
      // Extraer el token de la cookie si es necesario
      const token = response.data.access_token;
      if (token) {
        localStorage.setItem('token', token);
        axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error en login:', error);
      if (error.response?.status === 303) {
        // Manejar redirección especial
        const redirectUrl = error.response.headers.location;
        console.log('Redirección a:', redirectUrl);
      }
      throw new Error(error.response?.data?.detail || 'Error en la autenticación');
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    delete axiosInstance.defaults.headers.common['Authorization'];
  }
};

export default authService;