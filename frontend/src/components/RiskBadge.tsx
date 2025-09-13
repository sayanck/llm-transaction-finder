import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react';

interface RiskBadgeProps {
  level: 'high' | 'medium' | 'low';
  showIcon?: boolean;
  size?: 'sm' | 'md';
}

const RiskBadge: React.FC<RiskBadgeProps> = ({ 
  level, 
  showIcon = true, 
  size = 'md' 
}) => {
  const getIcon = () => {
    const iconSize = size === 'sm' ? 12 : 16;
    
    switch (level) {
      case 'high':
        return <AlertTriangle size={iconSize} />;
      case 'medium':
        return <AlertCircle size={iconSize} />;
      case 'low':
        return <CheckCircle size={iconSize} />;
      default:
        return null;
    }
  };

  const getClasses = () => {
    const baseClasses = size === 'sm' ? 'text-xs px-2 py-1' : 'text-sm px-3 py-1';
    
    switch (level) {
      case 'high':
        return `${baseClasses} badge-high`;
      case 'medium':
        return `${baseClasses} badge-medium`;
      case 'low':
        return `${baseClasses} badge-low`;
      default:
        return `${baseClasses} badge bg-gray-100 text-gray-800`;
    }
  };

  return (
    <span className={`badge ${getClasses()} inline-flex items-center gap-1`}>
      {showIcon && getIcon()}
      <span className="capitalize">{level} Risk</span>
    </span>
  );
};

export default RiskBadge;
