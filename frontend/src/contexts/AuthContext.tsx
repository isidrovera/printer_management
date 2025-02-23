// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../lib/axios'; // Importar tu instancia de Axios

// Interfaz de Usuario
interface User {
  id: number;
  username: string;
  email?: string;
  role?: string;
  must_change_password?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, userData: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Verificar autenticación al cargar
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          // Verificar token con endpoint de validación
          const response = await axiosInstance.get('/auth/me');
          setUser(response.data);
          setToken(storedToken);
        } catch (error) {
          // Token inválido, cerrar sesión
          logout();
        }
      }
    };

    checkAuth();
  }, []);

  const login = (newToken: string, userData: User) => {
    // Guardar token y usuario
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(userData);

    // Configurar token para futuras solicitudes
    axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

    // Navegar según el estado de contraseña
    if (userData.must_change_password) {
      navigate('/change-password');
    } else {
      navigate('/dashboard');
    }
  };

  const logout = async () => {
    try {
      // Cerrar sesión en backend
      await axiosInstance.post('/auth/logout');
    } catch (error) {
      console.error('Error al cerrar sesión', error);
    } finally {
      // Limpiar estado de autenticación
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
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
        isAuthenticated: !!token 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Hook personalizado para usar contexto de autenticación
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
};