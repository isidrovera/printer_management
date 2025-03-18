// src/lib/axios.ts
import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://161.132.39.159:8000/api/v1',  // 👈 URL completa del backend
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

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
        const tokenData = JSON.parse(tokenStr);
        config.headers.Authorization = `Bearer ${tokenData.access_token}`;
        console.log('🔑 Token added to request');
      } catch (error) {
        console.error('❌ Error parsing token:', error);
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

axiosInstance.interceptors.response.use(
  (response) => {
    console.log('📥 Response Success:', {
      status: response.status,
      url: response.config.url,
      data: response.data
    });
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', {
      status: error.response?.status,
      url: error.config?.url,
      data: error.response?.data,
      message: error.message
    });

    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;