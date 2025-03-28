// src/lib/axios.ts
import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'https://copierconnectremote.com/api/v1',  // URL completa del backend
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

axiosInstance.interceptors.request.use(
  (config) => {
    // NUEVO: Forzar HTTPS en todas las URLs
    if (config.url && config.url.startsWith('http://')) {
      config.url = config.url.replace('http://', 'https://');
      console.log('🔒 URL corregida a HTTPS:', config.url);
    }
    
    // NUEVO: Forzar HTTPS en baseURL si está configurado con HTTP
    if (config.baseURL && config.baseURL.startsWith('http://')) {
      config.baseURL = config.baseURL.replace('http://', 'https://');
      console.log('🔒 baseURL corregida a HTTPS:', config.baseURL);
    }
    
    // Construir fullUrl correctamente para depuración
    let fullUrl = config.url || '';
    if (config.baseURL && !config.url?.startsWith('http')) {
      fullUrl = `${config.baseURL}${config.url}`;
    }
    
    console.log('📤 Request:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      fullUrl: fullUrl
    });

    // Obtén el token de localStorage
    const tokenStr = localStorage.getItem('token');
    console.log('🔍 Token recuperado del localStorage:', tokenStr);
    
    if (tokenStr) {
      try {
        // Intenta analizar el token como JSON
        let authToken = '';
        
        try {
          const tokenData = JSON.parse(tokenStr);
          console.log('🔄 Token parseado como JSON:', tokenData);
          
          if (tokenData && tokenData.access_token) {
            authToken = tokenData.access_token;
            console.log('🔑 Usando access_token del objeto JSON:', authToken);
          } else if (tokenData && typeof tokenData === 'string') {
            authToken = tokenData;
            console.log('🔑 Usando el objeto JSON como string:', authToken);
          } else {
            // Fallback: usar el string completo
            authToken = tokenStr;
            console.log('🔑 Usando JSON completo como token:', authToken);
          }
        } catch (jsonError) {
          // Si no es JSON válido, usa el string directamente
          console.log('⚠️ El token no es un JSON válido, usando directamente:', tokenStr);
          authToken = tokenStr;
        }
        
        // Aplicar el token a la configuración
        if (authToken) {
          config.headers.Authorization = `Bearer ${authToken}`;
          console.log('✅ Token agregado a la solicitud:', `Bearer ${authToken.substring(0, 15)}...`);
        } else {
          console.warn('⚠️ Token vacío, no se agregó Authorization');
        }
      } catch (error) {
        console.error('❌ Error al procesar el token:', error);
        // No eliminar token aquí para no interrumpir la sesión por un error de procesamiento
      }
    } else {
      console.warn('⚠️ No hay token almacenado en localStorage');
    }
    
    console.log('🚀 Configuración final de la solicitud:', {
      url: config.url,
      method: config.method,
      headers: config.headers,
      hasAuthHeader: !!config.headers.Authorization
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
      url: response.config.url,
      dataPreview: typeof response.data === 'object' ? 
        JSON.stringify(response.data).substring(0, 100) + '...' : 
        response.data
    });
    
    // Si la respuesta contiene un token, mostrar en consola (útil para depuración)
    if (response.data && response.data.access_token) {
      console.log('🎫 Token recibido en respuesta:', response.data.access_token.substring(0, 15) + '...');
    }
    
    return response;
  },
  (error) => {
    // Extraer información detallada del error para depuración
    const errorInfo = {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      headers: error.config?.headers,
      hasAuthHeader: !!error.config?.headers?.Authorization,
      responseData: error.response?.data,
      message: error.message
    };
    
    console.error('❌ Error en respuesta:', errorInfo);
    
    // Manejo de errores específicos
    if (error.response?.status === 401) {
      console.warn('🔒 Error de autenticación (401), redirigiendo a login...');
      localStorage.removeItem('token');
      window.location.href = '/login';
    } else if (error.response?.status === 422) {
      console.error('📋 Error de validación (422):', error.response.data);
      // Mostrar los detalles específicos de validación si están disponibles
      if (error.response.data && error.response.data.detail) {
        console.error('📄 Detalles de validación:', error.response.data.detail);
      }
    }
    
    return Promise.reject(error);
  }
);

// Función de ayuda para depurar token (puedes llamarla desde consola)
axiosInstance.debugToken = () => {
  const tokenStr = localStorage.getItem('token');
  console.group('🔍 Depuración de token');
  console.log('Token en localStorage:', tokenStr);
  
  if (tokenStr) {
    try {
      const parsed = JSON.parse(tokenStr);
      console.log('Token parseado como JSON:', parsed);
      if (parsed.access_token) {
        console.log('access_token encontrado:', parsed.access_token);
      }
    } catch (e) {
      console.log('El token no es un JSON válido');
    }
  } else {
    console.log('No hay token almacenado');
  }
  console.groupEnd();
};

export default axiosInstance;