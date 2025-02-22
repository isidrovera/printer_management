// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../lib/axios';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  must_change_password: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const storedToken = localStorage.getItem('token');
        if (storedToken) {
          // Configura el token en axios
          axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          
          // Intenta obtener la información del usuario
          const response = await axiosInstance.get('/auth/me');
          setUser(response.data);
          setToken(storedToken);
        }
      } catch (error) {
        console.error('Error checking auth:', error);
        await logout();
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (newToken: string, userData: User) => {
    try {
      setToken(newToken);
      setUser(userData);
      localStorage.setItem('token', newToken);
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

      if (userData.must_change_password) {
        navigate('/change-password');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Error during login:', error);
      await logout();
    }
  };

  const logout = async () => {
    try {
      await axiosInstance.post('/auth/logout');
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem('token');
      delete axiosInstance.defaults.headers.common['Authorization'];
      navigate('/login');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token && !!user,
        isLoading
      }}
    >
      {!isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};