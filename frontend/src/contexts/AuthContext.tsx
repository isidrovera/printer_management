// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../lib/axios';
import { User, TokenResponse, LoginCredentials, LoginResponse } from '../types/auth';

interface AuthContextType {
  user: User | null;
  token: TokenResponse | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<TokenResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const tokenData: TokenResponse = JSON.parse(storedToken);
          setToken(tokenData);
          axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
          
          const response = await axiosInstance.get<User>('/auth/me');
          setUser(response.data);
        } catch (error) {
          console.error('Error en la inicialización de auth:', error);
          await logout();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // src/contexts/AuthContext.tsx
  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await axiosInstance.post<LoginResponse>('/auth/login', credentials);
      const { access_token, user: userData } = response.data;
      
      // Guardamos solo el token
      localStorage.setItem('token', access_token);
      
      // Actualizamos el estado
      setToken(access_token);
      setUser(userData);
      
      // Configuramos el header por defecto
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      if (userData.must_change_password) {
        navigate('/change-password');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Error en login:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (token?.access_token) {
        await axiosInstance.post('/auth/logout');
      }
    } catch (error) {
      console.error('Error en logout:', error);
    } finally {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      delete axiosInstance.defaults.headers.common['Authorization'];
      navigate('/login');
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      login,
      logout,
      isAuthenticated: !!token,
      isLoading
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
};