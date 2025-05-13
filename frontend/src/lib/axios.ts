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
  withCredentials: false,
  // Propiedad crítica: no permitir URLs absolutas (Novedad en Axios v1.x)
  allowAbsoluteUrls: false
});

// Log de la instancia creada
console.log('✅ Instancia axios creada con configuración:', {
  baseURL: axiosInstance.defaults.baseURL,
  headers: axiosInstance.defaults.headers,
  withCredentials: axiosInstance.defaults.withCredentials
});

// Función para verificar si una URL usa HTTP
const isHttpUrl = (url) => {
  if (!url) return false;
  return url.toLowerCase().startsWith('http:');
};

// Interceptor de solicitud
axiosInstance.interceptors.request.use(
  (config) => {
    try {
      // Registro inicial
      console.log('📝 Configuración original de solicitud:', {
        method: config.method?.toUpperCase(),
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

      // CONFIGURACIÓN CRÍTICA: Forzar HTTPS para todas las URLs
      // Para URLs que comienzan con http:
      if (config.url && config.url.startsWith('http:')) {
        console.warn('🔄 Cambiando URL de HTTP a HTTPS:', config.url);
        config.url = config.url.replace('http:', 'https:');
      }
      
      // Para baseURL que comienza con http:
      if (config.baseURL && config.baseURL.startsWith('http:')) {
        console.warn('🔄 Cambiando baseURL de HTTP a HTTPS:', config.baseURL);
        config.baseURL = config.baseURL.replace('http:', 'https:');
      }
      
      // SOLUCIÓN ESPECÍFICA PARA DRIVERS
      if (config.url && (
          config.url === '/drivers' || 
          config.url.includes('/drivers/') || 
          (config.url.startsWith('http') && config.url.includes('/drivers'))
        )) {
        console.log('🔧 Aplicando tratamiento especial para ruta /drivers');
        
        // Si es una URL relativa, convertirla en absoluta
        if (!config.url.startsWith('http')) {
          const baseURL = config.baseURL || API_BASE_URL;
          const absoluteUrl = baseURL + (config.url.startsWith('/') ? config.url : `/${config.url}`);
          
          // Asegurarse que usa HTTPS
          const finalUrl = absoluteUrl.replace('http:', 'https:');
          
          console.log('🔄 Convirtiendo URL relativa a absoluta para /drivers:', {
            original: config.url,
            absoluta: finalUrl
          });
          
          // Establecer la URL absoluta directamente
          config.url = finalUrl;
          config.baseURL = '';
        } 
        // Si ya es absoluta, asegurarse que usa HTTPS
        else if (config.url.startsWith('http:')) {
          config.url = config.url.replace('http:', 'https:');
          console.log('🔄 Forzando HTTPS para URL absoluta de /drivers:', config.url);
        }
      }

      // Verificación final
      const finalUrl = config.baseURL 
          ? `${config.baseURL}${config.url?.startsWith('/') ? config.url : `/${config.url}`}` 
          : config.url;
          
      console.log('📤 Solicitud final:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        baseURL: config.baseURL,
        finalUrl: finalUrl
      });

      return config;
    } catch (error) {
      console.error('❌ Error en interceptor de solicitud:', error);
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
    console.log('📥 Respuesta exitosa:', {
      status: response.status,
      statusText: response.statusText,
      url: response.config?.url
    });
    
    // Verificar si hay redirección (para debug)
    if (response.request?.responseURL) {
      console.log('🔄 URL de respuesta:', response.request.responseURL);
      
      if (isHttpUrl(response.request.responseURL)) {
        console.warn('⚠️ ALERTA: La respuesta viene de una URL HTTP:', response.request.responseURL);
      }
    }
    
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
    
    // Error de red específico (para debug)
    if (error.code === 'ERR_NETWORK') {
      console.error('🌐 Error de red detectado:', {
        message: error.message,
        url: error.config?.url
      });
      
      if (error.message && error.message.includes('Mixed Content')) {
        console.error('🔒 Error de contenido mixto (HTTP vs HTTPS)');
      }
    }

    if (error.response?.status === 401) {
      console.warn('🔒 Error de autenticación (401), redirigiendo a login...');
      localStorage.removeItem('token');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

// SOLUCIÓN ADICIONAL: Interceptar XMLHttpRequest a nivel global
// Esta es una medida de última instancia para asegurar que ninguna solicitud use HTTP
const originalOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function() {
  const args = Array.from(arguments);
  const url = args[1];
  
  if (typeof url === 'string' && url.startsWith('http:')) {
    console.warn('⚠️ INTERCEPTANDO XMLHttpRequest con HTTP y cambiando a HTTPS:', url);
    args[1] = url.replace('http:', 'https:');
  }
  
  return originalOpen.apply(this, args);
};

console.log('✅ Configuración de axios completada con protecciones HTTPS.');

export default axiosInstance;