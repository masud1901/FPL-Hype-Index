'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface PixelCardProps {
  children: ReactNode;
  title?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  className?: string;
}

export const PixelCard = ({ 
  children, 
  title, 
  variant = 'default',
  className = ''
}: PixelCardProps) => {
  const baseClasses = 'pixel-card';
  const variantClasses = `pixel-card-${variant}`;

  return (
    <motion.div
      className={`${baseClasses} ${variantClasses} ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {title && (
        <div className="mb-4">
          <h3 className="pixel-subtitle">{title}</h3>
        </div>
      )}
      <div className="pixel-card-body">
        {children}
      </div>
    </motion.div>
  );
}; 