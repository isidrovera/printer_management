// src/lib/axios.ts
import axios from 'axios';

// Configuración con URL absoluta HTTPS
const API_BASE_URL = 'https://copierconnectremote.com/api/v1';

// Log para indicar el inicio de la configuración
console.log('🔧 Iniciando configuración de axios con baseURL:', API_BASE_URL);

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  },
  withCredentials: false
});

// Log de la instancia creada
console.log('✅ Instancia axios creada con configuración:', {
  baseURL: axiosInstance.defaults.baseURL,
  headers: axiosInstance.defaults.headers,
  withCredentials: axiosInstance.defaults.withCredentials
});

// Función para registrar la URL final (solo para logs)
const getFullUrl = (config) => {
  if (!config) return 'Sin configuración';
  
  const baseURL = config.baseURL || '';
  const url = config.url || '';
  
  if (url.startsWith('http')) {
    return url;
  }
  
  const joinedUrl = baseURL + (url.startsWith('/') ? url : `/${url}`);
  return joinedUrl;
};

// Función para verificar si una URL usa HTTP
const isHttpUrl = (url) => {
  if (!url) return false;
  return url.toLowerCase().startsWith('http:');
};

// Función para imprimir un objeto sin ciclos circulares
const safeStringify = (obj) => {
  try {
    return JSON.stringify(obj);
  } catch (error) {
    return `[No serializable: ${typeof obj}]`;
  }
};

// Interceptor de solicitud
axiosInstance.interceptors.request.use(
  (config) => {
    try {
      // Registro inicial detallado
      console.log('📝 Configuración original de solicitud:', {
        method: config.method?.toUpperCase(),
        baseURL: config.baseURL,
        url: config.url,
        headers: config.headers ? {...config.headers} : 'No headers',
        fullUrl: getFullUrl(config)
      });

      // Verificar si alguna URL está usando HTTP
      if (isHttpUrl(config.url)) {
        console.warn('⚠️ ALERTA: config.url está usando HTTP:', config.url);
      }

      if (isHttpUrl(config.baseURL)) {
        console.warn('⚠️ ALERTA: config.baseURL está usando HTTP:', config.baseURL);
      }

      if (isHttpUrl(getFullUrl(config))) {
        console.warn('⚠️ ALERTA: URL completa está usando HTTP:', getFullUrl(config));
      }

      // Token desde localStorage
      const tokenStr = localStorage.getItem('token');
      console.log('🔐 Token en localStorage:', tokenStr ? 'Presente' : 'No presente');

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
            console.log('Error al parsear JSON:', jsonError);
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

      // PASO IMPORTANTE: Forzar HTTPS para todas las URLs
      // 1. Verificar y corregir baseURL
      if (config.baseURL && config.baseURL.startsWith('http:')) {
        console.warn('🔄 Cambiando baseURL de HTTP a HTTPS:', config.baseURL);
        const oldBaseUrl = config.baseURL;
        config.baseURL = config.baseURL.replace('http:', 'https:');
        console.log('✅ baseURL actualizado:', oldBaseUrl, '->', config.baseURL);
      }

      // 2. Verificar y corregir url
      if (config.url && config.url.startsWith('http:')) {
        console.warn('🔄 Cambiando url de HTTP a HTTPS:', config.url);
        const oldUrl = config.url;
        config.url = config.url.replace('http:', 'https:');
        console.log('✅ url actualizado:', oldUrl, '->', config.url);
      }

      // Verificación final y corrección de URL completa
      const finalUrl = getFullUrl(config);
      console.log('🔍 URL final después de modificaciones:', finalUrl);

      if (isHttpUrl(finalUrl)) {
        console.warn('⚠️ La URL final SIGUE usando HTTP. Último intento de corrección.');
        // Si aún hay HTTP en la URL final, intentar reconstruir la URL completa
        if (finalUrl.startsWith('http:')) {
          const httpsUrl = finalUrl.replace('http:', 'https:');
          console.log('🔄 Reconstruyendo URL completa:', finalUrl, '->', httpsUrl);
          
          // Si es una URL absoluta, reemplazar completamente
          if (config.url && config.url.startsWith('http')) {
            config.url = httpsUrl;
            config.baseURL = ''; // Evitar problemas con baseURL
          } else if (config.baseURL) {
            // Si es relativa, actualizar baseURL
            config.baseURL = config.baseURL.replace('http:', 'https:');
          }
        }
      }

      // Verificación final
      console.log('📤 Solicitud final:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        baseURL: config.baseURL,
        finalUrl: getFullUrl(config),
        headers: config.headers ? {...config.headers} : 'No headers'
      });

      return config;
    } catch (error) {
      console.error('❌ Error GRAVE en interceptor de solicitud:', error);
      return config; // Devolver config original para no bloquear la solicitud
    }
  },
  (error) => {
    console.error('❌ Error en solicitud:', error);
    return Promise.reject(error);
  }
);

// Interceptor de respuesta
axiosInstance.interceptors.response.use(
  (response) => {
    try {
      console.log('📥 Respuesta exitosa:', {
        status: response.status,
        statusText: response.statusText,
        url: response.config?.url,
        baseURL: response.config?.baseURL,
        finalUrl: getFullUrl(response.config),
        data: response.data ? 'Datos recibidos' : 'Sin datos',
        contentType: response.headers?.['content-type']
      });
      
      // Si hay redirección, verificar
      if (response.request?.responseURL) {
        console.log('🔄 URL de respuesta:', response.request.responseURL);
        
        if (isHttpUrl(response.request.responseURL)) {
          console.warn('⚠️ ALERTA: La respuesta viene de una URL HTTP:', 
            response.request.responseURL);
        }
      }
      
      return response;
    } catch (error) {
      console.error('❌ Error al procesar respuesta exitosa:', error);
      return response;
    }
  },
  (error) => {
    try {
      const errorInfo = {
        status: error.response?.status,
        statusText: error.response?.statusText,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
        finalUrl: getFullUrl(error.config),
        method: error.config?.method,
        hasAuthHeader: !!error.config?.headers?.Authorization,
        message: error.message
      };

      console.error('❌ Error en respuesta:', errorInfo);
      
      // Información detallada del error
      if (error.request) {
        console.error('📡 Información de la solicitud fallida:', {
          responseURL: error.request.responseURL,
          statusText: error.request.statusText,
          responseType: error.request.responseType,
          withCredentials: error.request.withCredentials,
          timeout: error.request.timeout
        });
        
        // Verificar si hay un problema de protocolo
        if (error.request.responseURL && isHttpUrl(error.request.responseURL)) {
          console.error('⚠️ ALERTA CRÍTICA: Respuesta fallida desde URL HTTP:', 
            error.request.responseURL);
        }
      }
      
      // Error de red específico
      if (error.code === 'ERR_NETWORK') {
        console.error('🌐 Error de red detectado:', {
          message: error.message,
          url: error.config?.url,
          protocol: error.config?.url?.split('://')[0]
        });
        
        // Verificar si es un problema de Mixed Content
        if (error.message.includes('Mixed Content')) {
          console.error('🔒 Error de contenido mixto (HTTP vs HTTPS)');
        }
      }

      if (error.response?.status === 401) {
        console.warn('🔒 Error de autenticación (401), redirigiendo a login...');
        localStorage.removeItem('token');
        window.location.href = '/login';
      }

      return Promise.reject(error);
    } catch (unexpectedError) {
      console.error('❌ Error inesperado al procesar el error:', unexpectedError);
      return Promise.reject(error);
    }
  }
);

// Log final de configuración completa
console.log('✅ Configuración de axios completada.');

export default axiosInstance;