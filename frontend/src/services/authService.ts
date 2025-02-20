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
      // Usar el nuevo endpoint api-login
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axiosInstance.post('/auth/api-login', formData);
      
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
  }
};