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

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await axiosInstance.post<LoginResponse>('/auth/login', credentials);
      const { user: userData, token: tokenData } = response.data;

      // Guardar token
      localStorage.setItem('token', JSON.stringify(tokenData));
      setToken(tokenData);
      setUser(userData);

      // Configurar token para futuras solicitudes
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;

      // Manejar flujo de 2FA si es necesario
      if (response.data.requires_2fa) {
        navigate('/2fa-verify');
        return;
      }

      // Manejar cambio de contraseña obligatorio
      if (userData.must_change_password) {
        navigate('/change-password');
        return;
      }

      navigate('/dashboard');
    } catch (error) {
      console.error('Error en login:', error);
      throw error;
    }
  };

  const refreshToken = async () => {
    try {
      if (!token?.refresh_token) throw new Error('No hay refresh token');

      const response = await axiosInstance.post<TokenResponse>('/auth/refresh', {
        refresh_token: token.refresh_token
      });

      const newToken = response.data;
      localStorage.setItem('token', JSON.stringify(newToken));
      setToken(newToken);
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${newToken.access_token}`;

      return newToken;
    } catch (error) {
      console.error('Error refrescando token:', error);
      await logout();
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