// src/lib/axios.ts
import axios from 'axios';

// Configuración básica de axios
const axiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Variables para manejar la actualización de tokens
let isRefreshing = false;
let failedQueue = [];

// Procesar la cola de solicitudes fallidas
const processQueue = (error, token = null) => {
  failedQueue.forEach(promise => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  
  failedQueue = [];
};

// Interceptor para las solicitudes
axiosInstance.interceptors.request.use(
  (config) => {
    console.log('📤 Request:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      fullUrl: `${config.baseURL}${config.url}`
    });

    const tokenStr = localStorage.getItem('token');
    if (tokenStr) {
      try {
        config.headers.Authorization = `Bearer ${tokenStr}`;
        console.log('🔑 Token added to request');
      } catch (error) {
        console.error('❌ Error applying token:', error);
        localStorage.removeItem('token');
      }
    }
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Interceptor para las respuestas
axiosInstance.interceptors.response.use(
  (response) => {
    console.log('📥 Response Success:', {
      status: response.status,
      url: response.config.url,
      data: response.data
    });
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    console.error('❌ Response Error:', {
      status: error.response?.status,
      url: originalRequest?.url,
      data: error.response?.data,
      message: error.message
    });

    // Manejo de token expirado (401)
    if (error.response?.status === 401 && 
        error.response?.data?.detail === 'Token expirado' && 
        !originalRequest._retry) {
      
      if (isRefreshing) {
        // Si ya estamos actualizando, añadir a la cola
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return axiosInstance(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Obtener refresh token del almacenamiento
        const refreshToken = localStorage.getItem('refreshToken');
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Llamar al endpoint de renovación
        const response = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken
        });

        // Guardar nuevos tokens
        const { access_token, refresh_token } = response.data;
        localStorage.setItem('token', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        
        // Actualizar el token en la solicitud original
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
        
        // Procesar cola y reintentar solicitud original
        processQueue(null, access_token);
        isRefreshing = false;
        
        return axiosInstance(originalRequest);
        
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        
        // Limpiar tokens y redirigir al login
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        window.location.href = '/login';
        
        return Promise.reject(refreshError);
      }
    }

    // Para otros errores 401, limpiar y redirigir
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

export default axiosInstance;