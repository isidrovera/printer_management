// src/components/ui/alert.tsx
import React from 'react';

interface AlertProps {
  children: React.ReactNode;
  variant?: 'default' | 'destructive';
  className?: string;
}

export const Alert = ({ 
  children, 
  variant = 'default',
  className = '' 
}: AlertProps) => {
  const variantStyles = {
    default: 'bg-blue-50 text-blue-700 border-blue-200',
    destructive: 'bg-red-50 text-red-700 border-red-200'
  };

  return (
    <div className={`p-4 rounded-md border ${variantStyles[variant]} ${className}`}>
      {children}
    </div>
  );
};