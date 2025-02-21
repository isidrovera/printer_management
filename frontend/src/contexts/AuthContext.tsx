import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Configurar la base URL de axios
axios.defaults.baseURL = '/api';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  full_name?: string;
  must_change_password: boolean;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  login: (token: string, userData: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // Verificar si hay un token guardado al cargar la aplicación
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      console.log('Restaurando sesión de usuario desde localStorage');
      try {
        const userData = JSON.parse(savedUser);
        setUser(userData);
        
        // Configurar el token en axios
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        console.log('Token restaurado en axios headers');
      } catch (error) {
        console.error('Error al restaurar la sesión:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    } else {
      console.log('No hay sesión activa');
    }
  }, []);

  const login = (token: string, userData: User) => {
    console.log('Iniciando sesión para usuario:', userData.username);
    setUser(userData);
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    console.log('Datos de sesión guardados correctamente');
  };

  const logout = () => {
    console.log('Cerrando sesión');
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    console.log('Sesión cerrada y datos limpiados');
  };

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user
  };

  console.log('Estado actual de autenticación:', !!user);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    console.error('useAuth debe ser usado dentro de un AuthProvider');
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};