// src/lib/axios.ts
import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '', // URL base de tu API
  withCredentials: true, // Importante para manejar cookies/credenciales
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Interceptor para manejar errores de autorización
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Manejar específicamente errores de autorización
    if (error.response?.status === 401) {
      // Redirigir al login o cerrar sesión
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;