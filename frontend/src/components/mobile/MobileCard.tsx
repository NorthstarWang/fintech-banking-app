import React from 'react';
import { motion } from 'framer-motion';
import Card from '../ui/Card';

interface MobileCardProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  variant?: 'default' | 'prominent' | 'subtle' | 'stats';
  animated?: boolean;
  index?: number;
}

export const MobileCard: React.FC<MobileCardProps> = ({
  children,
  onClick,
  className = '',
  variant = 'default',
  animated = true,
  index = 0,
}) => {
  const cardContent = (
    <Card
      variant={variant}
      onClick={onClick}
      hoverable={!!onClick}
      className={`
        ${className}
        touch-manipulation
        active:scale-[0.98]
        transition-transform
        duration-100
      `}
    >
      {children}
    </Card>
  );

  if (!animated) return cardContent;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        delay: index * 0.05,
        type: 'spring',
        stiffness: 300,
        damping: 25
      }}
      whileTap={{ scale: 0.98 }}
    >
      {cardContent}
    </motion.div>
  );
};

// Mobile-optimized card header with touch-friendly sizing
export const MobileCardHeader: React.FC<{
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}> = ({ title, subtitle, action, icon }) => (
  <div className="flex items-start justify-between p-4 pb-0">
    <div className="flex items-start gap-3 flex-1">
      {icon && (
        <div className="p-2 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] flex-shrink-0">
          {icon}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-[var(--text-1)] text-base truncate">
          {title}
        </h3>
        {subtitle && (
          <p className="text-sm text-[var(--text-2)] mt-1">
            {subtitle}
          </p>
        )}
      </div>
    </div>
    {action && (
      <div className="ml-2 flex-shrink-0">
        {action}
      </div>
    )}
  </div>
);

// Mobile-optimized card content with proper spacing
export const MobileCardContent: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`p-4 ${className}`}>
    {children}
  </div>
);

// Touch-friendly card footer
export const MobileCardFooter: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`p-4 pt-0 ${className}`}>
    {children}
  </div>
);

// Mobile-optimized stat card
export const MobileStatCard: React.FC<{
  label: string;
  value: string | number;
  trend?: {
    value: string;
    direction: 'up' | 'down';
  };
  icon?: React.ReactNode;
  color?: string;
  onClick?: () => void;
}> = ({ label, value, trend, icon, color, onClick }) => (
  <MobileCard variant="stats" onClick={onClick}>
    <div className="p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-[var(--text-2)]">{label}</span>
        {icon && (
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: color || 'rgba(var(--glass-rgb),0.1)' }}
          >
            {icon}
          </div>
        )}
      </div>
      <div className="space-y-1">
        <p className="text-2xl font-bold text-[var(--text-1)]">
          {value}
        </p>
        {trend && (
          <div className="flex items-center gap-1">
            <span className={`
              text-sm font-medium
              ${trend.direction === 'up' ? 'text-[var(--primary-emerald)]' : 'text-[var(--primary-red)]'}
            `}>
              {trend.direction === 'up' ? '↑' : '↓'} {trend.value}
            </span>
          </div>
        )}
      </div>
    </div>
  </MobileCard>
);

export default MobileCard;