// src/lib/axios.ts
import axios from 'axios';

// Configuración con URL absoluta HTTPS
const API_BASE_URL = 'https://copierconnectremote.com/api/v1';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  },
  withCredentials: false
});

axiosInstance.interceptors.request.use(
  (config) => {
    // Registro inicial
    console.log('Configuración original:', {
      baseURL: config.baseURL,
      url: config.url
    });

    // Token desde localStorage
    const tokenStr = localStorage.getItem('token');

    if (tokenStr) {
      try {
        let authToken = '';

        try {
          const tokenData = JSON.parse(tokenStr);

          if (tokenData && tokenData.access_token) {
            authToken = tokenData.access_token;
            console.log('🔑 Usando access_token del objeto JSON:', authToken.substring(0, 15) + '...');
          } else if (tokenData && typeof tokenData === 'string') {
            authToken = tokenData;
            console.log('🔑 Usando el objeto JSON como string:', authToken.substring(0, 15) + '...');
          } else {
            authToken = tokenStr;
            console.log('🔑 Usando JSON completo como token:', authToken.substring(0, 15) + '...');
          }
        } catch (jsonError) {
          authToken = tokenStr;
          console.log('⚠️ Token no es JSON válido, usando directamente:', authToken.substring(0, 15) + '...');
        }

        if (authToken) {
          config.headers.Authorization = `Bearer ${authToken}`;
          console.log('✅ Token agregado a la solicitud');
        } else {
          console.warn('⚠️ Token vacío, no se agregó Authorization');
        }
      } catch (error) {
        console.error('❌ Error al procesar el token:', error);
      }
    } else {
      console.warn('⚠️ No hay token almacenado en localStorage');
    }

    // Verificación final
    const finalUrl = config.baseURL && config.url && !config.url.startsWith('http')
      ? `${config.baseURL}${config.url.startsWith('/') ? config.url : `/${config.url}`}`
      : config.url || '';

    console.log('📤 Solicitud final:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      finalUrl: finalUrl
    });

    return config;
  },
  (error) => {
    console.error('❌ Error en solicitud:', error);
    return Promise.reject(error);
  }
);

axiosInstance.interceptors.response.use(
  (response) => {
    console.log('📥 Respuesta exitosa:', {
      status: response.status,
      url: response.config.url
    });
    return response;
  },
  (error) => {
    const errorInfo = {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      hasAuthHeader: !!error.config?.headers?.Authorization,
      message: error.message
    };

    console.error('❌ Error en respuesta:', errorInfo);

    if (error.response?.status === 401) {
      console.warn('🔒 Error de autenticación (401), redirigiendo a login...');
      localStorage.removeItem('token');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
