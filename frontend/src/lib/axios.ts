// src/lib/axios.ts
import axios from 'axios';

// Configuración con URL absoluta HTTPS
// Importante: Usamos la URL completa para evitar problemas de dominio cruzado
const API_BASE_URL = 'https://copierconnectremote.com/api/v1';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  },
  // Agregar withCredentials si necesitas enviar cookies entre dominios
  withCredentials: false
});

// Interceptor para asegurar que todas las URLs usen HTTPS
axiosInstance.interceptors.request.use(
  (config) => {
    // Registrar y verificar la configuración original de la solicitud
    console.log('Configuración original:', {
      baseURL: config.baseURL,
      url: config.url
    });

    // 1. Asegurar que la baseURL siempre use HTTPS
    if (config.baseURL && config.baseURL.startsWith('http://')) {
      config.baseURL = config.baseURL.replace('http://', 'https://');
      console.log('🔒 baseURL corregida a HTTPS:', config.baseURL);
    }

    // 2. Si la URL es absoluta, asegurar que use HTTPS
    if (config.url && config.url.startsWith('http://')) {
      config.url = config.url.replace('http://', 'https://');
      console.log('🔒 URL absoluta corregida a HTTPS:', config.url);
    }
    
    // 3. Modificación crucial: Si estamos en una ruta específica como /monitor/printers,
    // forzar el uso de una URL absoluta con HTTPS
    if (config.url && config.url.includes('/monitor/printers')) {
      // Solo modificar si no es ya una URL absoluta
      if (!config.url.startsWith('http')) {
        const originalUrl = config.url;
        // Crear URL absoluta
        config.url = `https://copierconnectremote.com/api/v1${config.url.startsWith('/') ? config.url : `/${config.url}`}`;
        // Eliminar baseURL para evitar que se agregue dos veces
        config.baseURL = '';
        console.log(`🔄 Ruta crítica detectada. Cambiando ${originalUrl} a URL absoluta: ${config.url}`);
      }
    }

    // Obtén el token de localStorage
    const tokenStr = localStorage.getItem('token');
    
    if (tokenStr) {
      try {
        // Intenta analizar el token como JSON
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
            // Fallback: usar el string completo
            authToken = tokenStr;
            console.log('🔑 Usando JSON completo como token:', authToken.substring(0, 15) + '...');
          }
        } catch (jsonError) {
          // Si no es JSON válido, usa el string directamente
          authToken = tokenStr;
          console.log('⚠️ El token no es un JSON válido, usando directamente:', authToken.substring(0, 15) + '...');
        }
        
        // Aplicar el token a la configuración
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
    
    // Verificación final de la URL completa que se enviará
    let finalUrl = '';
    if (config.baseURL && config.url && !config.url.startsWith('http')) {
      finalUrl = `${config.baseURL}${config.url.startsWith('/') ? config.url : `/${config.url}`}`;
    } else {
      finalUrl = config.url || '';
    }
    
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