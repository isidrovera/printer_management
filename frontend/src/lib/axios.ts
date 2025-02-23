// src/lib/axios.ts
// src/lib/axios.ts
import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: '/api/v1', // Usamos la ruta relativa para trabajar con el proxy de Vite
  withCredentials: true,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Interceptor para agregar el token a las peticiones
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        // Intentamos parsear el token como JSON primero
        const parsedToken = JSON.parse(token);
        config.headers.Authorization = `Bearer ${parsedToken.access_token}`;
      } catch {
        // Si no es JSON, lo usamos directamente
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login'; // Usamos /login en lugar de /auth/login
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;