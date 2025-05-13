// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axiosInstance from '../lib/axios';
import React, { useState } from 'react';
import { 
  LayoutDashboard,
  Users,
  Package,
  BookOpen,
  LogOut,
  PlusCircle,
  ChevronRight,
  BarChart3,
  PieChart,
  Globe,
  ArrowUpRight
} from 'lucide-react';

const DashboardCard = ({ icon: Icon, color, value, label, onClick }) => {
  return (
    <div 
      className="bg-white rounded-xl p-6 flex flex-col items-center cursor-pointer transition-all hover:shadow-md"
      style={{ backgroundColor: color }}
      onClick={onClick}
    >
      <div className="p-3 rounded-full bg-white bg-opacity-30 mb-4">
        <Icon className="h-6 w-6 text-white" />
      </div>
      <h2 className="text-2xl font-bold text-white">{value}</h2>
      <p className="text-white text-sm opacity-90">{label}</p>
    </div>
  );
};

const SidebarItem = ({ icon: Icon, label, active, onClick }) => {
  return (
    <div 
      className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all ${active ? 'bg-gray-100' : 'hover:bg-gray-50'}`}
      onClick={onClick}
    >
      <Icon className={`h-5 w-5 ${active ? 'text-blue-600' : 'text-gray-500'}`} />
      <span className={`${active ? 'text-blue-600 font-medium' : 'text-gray-700'}`}>{label}</span>
    </div>
  );
};

const Dashboard = () => {
  const [activePage, setActivePage] = useState('dashboard');
  
  const handleCardClick = (destination) => {
    console.log(`Navegando a: ${destination}`);
    // Aquí implementarías la navegación real
    setActivePage(destination);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 p-4 flex flex-col">
        <div className="flex items-center mb-6">
          <div className="text-blue-600 font-bold text-2xl">
            <span className="flex items-center">
              <Globe className="h-6 w-6 mr-2" />
              NetPrint
            </span>
          </div>
        </div>
        
        <div className="bg-gray-100 p-2 rounded-lg flex items-center space-x-3 mb-6">
          <div className="bg-yellow-500 h-8 w-8 rounded-lg flex items-center justify-center text-white font-medium">
            JF
          </div>
          <div>
            <p className="text-sm font-medium">Jayden Frankie</p>
          </div>
        </div>
        
        <nav className="flex-1 space-y-1">
          <SidebarItem 
            icon={LayoutDashboard} 
            label="Dashboard" 
            active={activePage === 'dashboard'} 
            onClick={() => setActivePage('dashboard')}
          />
          <SidebarItem 
            icon={Users} 
            label="Usuarios" 
            active={activePage === 'users'} 
            onClick={() => setActivePage('users')}
          />
          <SidebarItem 
            icon={Package} 
            label="Impresoras" 
            active={activePage === 'printers'} 
            onClick={() => setActivePage('printers')}
          />
          <SidebarItem 
            icon={BookOpen} 
            label="Reportes" 
            active={activePage === 'reports'} 
            onClick={() => setActivePage('reports')}
          />
          <SidebarItem 
            icon={PlusCircle} 
            label="Clientes" 
            active={activePage === 'clients'} 
            onClick={() => setActivePage('clients')}
          />
        </nav>
        
        <div className="mt-auto pt-4 border-t border-gray-200">
          <SidebarItem 
            icon={LogOut} 
            label="Cerrar sesión" 
            onClick={() => console.log('Cerrar sesión')}
          />
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Hola, Welcome back</h1>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="relative">
                <select className="appearance-none bg-white border border-gray-200 rounded-lg py-2 pl-3 pr-10 focus:outline-none">
                  <option>🇪🇸 ES</option>
                  <option>🇬🇧 EN</option>
                </select>
                <ChevronRight className="absolute right-3 top-1/2 transform -translate-y-1/2 -rotate-90 h-4 w-4 text-gray-500" />
              </div>
              
              <div className="relative">
                <div className="bg-white border border-gray-200 rounded-lg p-2 flex items-center justify-center">
                  <div className="relative">
                    <div className="h-2 w-2 bg-red-500 rounded-full absolute -top-0.5 -right-0.5"></div>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="bg-orange-100 h-8 w-8 rounded-lg flex items-center justify-center text-orange-800 font-medium">
                JF
              </div>
            </div>
          </div>
          
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <DashboardCard 
              icon={BarChart3} 
              color="#e6f2ff" 
              value="714k" 
              label="Impresiones Semanales" 
              onClick={() => handleCardClick('stats_weekly')}
            />
            
            <DashboardCard 
              icon={Users} 
              color="#e1f5fe" 
              value="1.35m" 
              label="Usuarios Nuevos" 
              onClick={() => handleCardClick('new_users')}
            />
            
            <DashboardCard 
              icon={LayoutDashboard} 
              color="#fff8e1" 
              value="1.72m" 
              label="Total Impresoras" 
              onClick={() => handleCardClick('total_printers')}
            />
            
            <DashboardCard 
              icon={PlusCircle} 
              color="#ffebee" 
              value="234" 
              label="Bug Reports" 
              onClick={() => handleCardClick('bug_reports')}
            />
          </div>
          
          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">Actividad Impresoras</h2>
                  <p className="text-sm text-gray-500">+14.5% más que el año pasado</p>
                </div>
                <button className="text-blue-600 text-sm font-medium flex items-center">
                  Ver detalles
                  <ArrowUpRight className="h-4 w-4 ml-1" />
                </button>
              </div>
              
              <div className="flex mb-4 space-x-4">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-blue-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Team A</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-yellow-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Team B</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-green-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Team C</span>
                </div>
              </div>
              
              {/* Simple chart representation */}
              <div className="h-64 flex items-end space-x-2">
                {[40, 20, 60, 30, 50, 25, 70, 35, 55, 45, 65, 30].map((height, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    {index % 3 === 0 && (
                      <div 
                        className="w-full mb-2 rounded-sm"
                        style={{ 
                          height: `${height * 0.6}%`,
                          backgroundColor: '#4285F4'
                        }}
                      ></div>
                    )}
                    <div
                      className="w-full relative group"
                      style={{ height: `${height}%` }}
                    >
                      <div className="w-full absolute bottom-0 left-0 bg-blue-100 rounded-sm">
                        <div 
                          className="absolute bottom-0 left-0 w-full bg-blue-500 rounded-sm transition-all duration-300"
                          style={{ height: '100%' }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex justify-between mt-4">
                <span className="text-xs text-gray-500">Ene</span>
                <span className="text-xs text-gray-500">Feb</span>
                <span className="text-xs text-gray-500">Mar</span>
                <span className="text-xs text-gray-500">Abr</span>
                <span className="text-xs text-gray-500">May</span>
                <span className="text-xs text-gray-500">Jun</span>
                <span className="text-xs text-gray-500">Jul</span>
                <span className="text-xs text-gray-500">Ago</span>
                <span className="text-xs text-gray-500">Sep</span>
                <span className="text-xs text-gray-500">Oct</span>
                <span className="text-xs text-gray-500">Nov</span>
                <span className="text-xs text-gray-500">Dic</span>
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">Distribución Clientes</h2>
                  <p className="text-sm text-gray-500">Actual</p>
                </div>
                <button className="text-blue-600 text-sm font-medium flex items-center">
                  Ver detalles
                  <ArrowUpRight className="h-4 w-4 ml-1" />
                </button>
              </div>
              
              <div className="flex justify-center">
                <div className="w-64 h-64 relative">
                  {/* Simple pie chart representation */}
                  <div className="relative">
                    <svg viewBox="0 0 100 100" className="w-full h-full">
                      {/* Blue segment - 27% */}
                      <path 
                        d="M50,50 L97,50 A47,47 0 0,1 85.35,85.35 Z" 
                        fill="#4285F4"
                      />
                      
                      {/* Red segment - 34% */}
                      <path 
                        d="M50,50 L85.35,85.35 A47,47 0 0,1 33.98,96.98 Z" 
                        fill="#EA4335"
                      />
                      
                      {/* Yellow segment - 13% */}
                      <path 
                        d="M50,50 L33.98,96.98 A47,47 0 0,1 3,50 Z" 
                        fill="#FBBC05"
                      />
                      
                      {/* Green segment - 26% */}
                      <path 
                        d="M50,50 L3,50 A47,47 0 0,1 50,3 L50,50 Z" 
                        fill="#34A853"
                      />
                      
                      <circle cx="50" cy="50" r="30" fill="white" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-blue-500 mr-2"></div>
                  <span className="text-sm text-gray-600">América (27%)</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-red-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Asia (34%)</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-yellow-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Europa (13%)</span>
                </div>
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-green-500 mr-2"></div>
                  <span className="text-sm text-gray-600">África (26%)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;