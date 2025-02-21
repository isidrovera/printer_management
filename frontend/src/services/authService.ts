// src/services/authService.ts
import axios from 'axios';

const API_URL = 'http://161.132.39.159:8000/api/v1';

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
  },
  withCredentials: true
});

// Interceptor para manejar errores
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username: string, password: string) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axiosInstance.post('/auth/api-login', formData);
      
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        // Configurar token para futuras peticiones
        axiosInstance.defaults.headers.common['Authorization'] = 
          `Bearer ${response.data.access_token}`;
        
        // Manejar redirección si es necesario cambiar la contraseña
        if (response.data.user?.must_change_password) {
          return {
            ...response.data,
            redirect: '/auth/change-password'
          };
        }
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
    localStorage.removeItem('user');
    delete axiosInstance.defaults.headers.common['Authorization'];
  },

  getToken: () => {
    return localStorage.getItem('token');
  },

  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  }
};

// Configurar interceptor para incluir el token en todas las peticiones
axiosInstance.interceptors.request.use(
  (config) => {
    const token = authService.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default authService;