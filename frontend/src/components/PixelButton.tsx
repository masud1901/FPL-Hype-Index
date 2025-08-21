'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface PixelButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'warning' | 'danger' | 'default';
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const PixelButton = ({ 
  children, 
  onClick, 
  variant = 'default', 
  disabled = false,
  className = '',
  type = 'button'
}: PixelButtonProps) => {
  const baseClasses = 'pixel-button';
  const variantClasses = `pixel-button-${variant}`;
  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';

  return (
    <motion.button
      className={`${baseClasses} ${variantClasses} ${disabledClasses} ${className}`}
      onClick={onClick}
      disabled={disabled}
      type={type}
      whileHover={!disabled ? { y: -2 } : {}}
      whileTap={!disabled ? { y: 0 } : {}}
      transition={{ duration: 0.1 }}
    >
      {children}
    </motion.button>
  );
}; 