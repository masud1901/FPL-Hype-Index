'use client';

import { motion } from 'framer-motion';

interface PixelProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  className?: string;
}

export const PixelProgressBar = ({ 
  value, 
  max = 10, 
  label,
  showValue = true,
  className = ''
}: PixelProgressBarProps) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  return (
    <div className={`pixel-progress-container ${className}`}>
      {label && (
        <div className="pixel-body mb-2">{label}</div>
      )}
      <div className="pixel-progress-bar">
        <motion.div 
          className="pixel-progress-fill"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
      {showValue && (
        <div className="pixel-body mt-2 text-right">
          {value.toFixed(1)}/{max}
        </div>
      )}
    </div>
  );
}; 