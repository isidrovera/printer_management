// src/pages/Dashboard.tsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Dashboard = () => {
  const { user } = useAuth();

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p>Bienvenido, {user?.username}!</p>
    </div>
  );
};

export default Dashboard;