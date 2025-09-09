import React from 'react';
import { LucideIcon, ArrowUpRight, ArrowDownLeft } from 'lucide-react';
import Card from '../ui/Card';
import { useHoverTracking } from '@/hooks/useHoverTracking';

interface StatCardProps {
  label: string;
  value: string;
  trend: 'up' | 'down';
  change: string;
  icon: LucideIcon;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, trend, change, icon: Icon }) => {
  const hoverProps = useHoverTracking({
    elementId: `stat-card-${label.toLowerCase().replace(/\s+/g, '-')}`,
    elementName: `${label}: ${value}`
  });

  return (
    <Card 
      variant="stats" 
      className="p-6 cursor-pointer transition-all hover:border-[var(--border-2)]"
      data-testid={`stat-card-${label.toLowerCase().replace(/\s+/g, '-')}`}
      {...hoverProps}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-[var(--text-2)]">{label}</p>
          <p className="text-2xl font-bold text-[var(--text-1)] mt-1">
            {value}
          </p>
          <div className="flex items-center mt-2 gap-1">
            {trend === 'up' ? (
              <ArrowUpRight className="w-4 h-4 text-[var(--primary-emerald)]" />
            ) : (
              <ArrowDownLeft className="w-4 h-4 text-[var(--primary-red)]" />
            )}
            <span
              className={`text-sm font-medium ${
                trend === 'up'
                  ? 'text-[var(--primary-emerald)]'
                  : 'text-[var(--primary-red)]'
              }`}
            >
              {change}
            </span>
            <span className="text-xs text-[var(--text-2)]">
              vs last month
            </span>
          </div>
        </div>
        <div className="p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.3)]">
          <Icon className="w-6 h-6 text-[var(--primary-blue)]" />
        </div>
      </div>
    </Card>
  );
};

export default StatCard;