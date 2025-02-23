// src/lib/axios.ts
import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: '/api/v1', // Directamente usando la ruta del proxy
  withCredentials: true,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Interceptor para manejar errores de autorización
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;