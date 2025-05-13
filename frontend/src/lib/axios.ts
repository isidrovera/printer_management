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

    // MEJORA CRUCIAL: Asegurar que TODAS las solicitudes usen HTTPS
    
    // 1. Asegurar que la baseURL siempre use HTTPS
    if (config.baseURL && !config.baseURL.startsWith('https://')) {
      config.baseURL = config.baseURL.replace(/^http:\/\//i, 'https://');
      console.log('🔒 baseURL corregida a HTTPS:', config.baseURL);
    }

    // 2. Si la URL es absoluta, asegurar que use HTTPS
    if (config.url && config.url.startsWith('http://')) {
      config.url = config.url.replace(/^http:\/\//i, 'https://');
      console.log('🔒 URL absoluta corregida a HTTPS:', config.url);
    }
    
    // 3. SOLUCIÓN PARA MIXED CONTENT: Forzar URLs absolutas para rutas problemáticas
    // Lista de rutas problemáticas conocidas
    const criticalPaths = ['/drivers', '/printer-oids', '/monitor/printers'];
    
    // Verificar si la URL contiene alguna de las rutas críticas
    const isCriticalPath = config.url && criticalPaths.some(path => 
      config.url?.includes(path) || config.url?.startsWith(path)
    );
    
    // Si es una ruta crítica y no es ya una URL absoluta, convertirla a URL absoluta con HTTPS
    if (isCriticalPath && config.url && !config.url.startsWith('http')) {
      const originalUrl = config.url;
      // Crear URL absoluta
      config.url = `https://copierconnectremote.com/api/v1${config.url.startsWith('/') ? config.url : `/${config.url}`}`;
      // Eliminar baseURL para evitar que se agregue dos veces
      config.baseURL = '';
      console.log(`🔄 Ruta crítica detectada. Cambiando ${originalUrl} a URL absoluta: ${config.url}`);
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
    
    // VALIDACIÓN FINAL: asegurar que la URL final siempre comience con HTTPS
    if (finalUrl.startsWith('http://')) {
      console.warn('⚠️ Aún detectada URL final con HTTP, corrigiendo...');
      // Substituir solo el principio de la URL
      const correctedUrl = finalUrl.replace(/^http:\/\//i, 'https://');
      
      // Si la URL es relativa al baseURL, ajustar
      if (config.url && !config.url.startsWith('http')) {
        config.baseURL = correctedUrl.substring(0, correctedUrl.length - config.url.length);
      } else {
        // Si es absoluta, ajustar directamente la URL
        config.url = correctedUrl;
        config.baseURL = '';
      }
      
      finalUrl = correctedUrl;
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