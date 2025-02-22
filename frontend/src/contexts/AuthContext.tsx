// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../lib/axios';

// Define a more robust User interface
interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  must_change_password?: boolean;
}

// Default user object to prevent undefined errors
const defaultUser: User = {
  id: 0,
  username: '',
  email: '',
  role: '',
  must_change_password: false
};

interface AuthContextType {
  user: User;
  token: string | null;
  login: (token: string, userData: User) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User>(defaultUser);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const storedToken = localStorage.getItem('token');
        if (storedToken) {
          // Configure token in axios
          axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          
          // Try to get user information
          const response = await axiosInstance.get('/auth/me');
          
          // Ensure response has user data
          if (response.data) {
            setUser(response.data);
            setToken(storedToken);
          } else {
            await logout();
          }
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
      // Validate input
      if (!newToken || !userData) {
        throw new Error('Invalid login credentials');
      }

      // Set token and user
      setToken(newToken);
      setUser(userData);

      // Store token in local storage
      localStorage.setItem('token', newToken);

      // Set authorization header
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

      // Check if password change is required
      const mustChangePassword = userData.must_change_password ?? false;

      // Navigate based on password change requirement
      if (mustChangePassword) {
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
      // Attempt to call logout endpoint
      await axiosInstance.post('/auth/logout');
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      // Reset authentication state
      setToken(null);
      setUser(defaultUser);
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
        isAuthenticated: !!token && user.id !== 0,
        isLoading
      }}
    >
      {!isLoading && children}
    </AuthContext.Provider>
  );
};

// Custom hook with improved error handling
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};