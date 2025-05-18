'use client';

import { motion } from 'framer-motion';

interface LoadingSkeletonProps {
  type?: 'page' | 'card' | 'list' | 'chart' | 'component' | 'text' | 'image';
  className?: string;
  count?: number;
  height?: string | number;
  width?: string | number;
}

export default function LoadingSkeleton({ 
  type = 'card', 
  className = '',
  count = 1,
  height,
  width
}: LoadingSkeletonProps) {
  const shimmer = {
    initial: { backgroundPosition: '-200% 0' },
    animate: { 
      backgroundPosition: '200% 0',
      transition: {
        repeat: Infinity,
        duration: 1.5,
        ease: 'linear'
      }
    }
  };

  const baseClasses = `
    skeleton
    bg-[length:200%_100%] rounded-lg
  `;

  const renderSkeleton = () => {
    switch (type) {
      case 'page':
        return (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <motion.div {...shimmer} className={`${baseClasses} h-12 w-64 mb-8`} />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <motion.div key={i} {...shimmer} className={`${baseClasses} h-48`} />
              ))}
            </div>
          </div>
        );

      case 'card':
        return (
          <motion.div 
            {...shimmer} 
            className={`${baseClasses} p-6 ${className}`}
            style={{ height: height || '200px', width: width || '100%' }}
          >
            <div className="space-y-4">
              <div className="h-4 skeleton-item w-3/4" />
              <div className="h-4 skeleton-item w-1/2" />
              <div className="h-8 skeleton-item w-full mt-4" />
            </div>
          </motion.div>
        );

      case 'list':
        return (
          <div className="space-y-4">
            {[...Array(count)].map((_, i) => (
              <motion.div 
                key={i} 
                {...shimmer} 
                className={`${baseClasses} p-4 ${className}`}
                style={{ height: height || '80px', width: width || '100%' }}
              >
                <div className="flex items-center space-x-4">
                  <div className="h-12 w-12 skeleton-item rounded-full" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 skeleton-item w-3/4" />
                    <div className="h-3 skeleton-item w-1/2" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        );

      case 'chart':
        return (
          <motion.div 
            {...shimmer} 
            className={`${baseClasses} p-4 ${className}`}
            style={{ height: height || '300px', width: width || '100%' }}
          >
            <div className="h-full flex items-end space-x-2">
              {[...Array(7)].map((_, i) => (
                <div 
                  key={i} 
                  className="flex-1 skeleton-item rounded-t"
                  style={{ height: `${Math.random() * 80 + 20}%` }}
                />
              ))}
            </div>
          </motion.div>
        );

      case 'text':
        return (
          <div className="space-y-2">
            {[...Array(count)].map((_, i) => (
              <motion.div 
                key={i} 
                {...shimmer} 
                className={`${baseClasses} h-4 ${className}`}
                style={{ width: width || `${Math.random() * 40 + 60}%` }}
              />
            ))}
          </div>
        );

      case 'image':
        return (
          <motion.div 
            {...shimmer} 
            className={`${baseClasses} ${className}`}
            style={{ height: height || '200px', width: width || '100%' }}
          />
        );

      default:
        return (
          <motion.div 
            {...shimmer} 
            className={`${baseClasses} ${className}`}
            style={{ height: height || '100px', width: width || '100%' }}
          />
        );
    }
  };

  return renderSkeleton();
}

// Specific skeleton components for common use cases
export function TransactionSkeleton() {
  return <LoadingSkeleton type="list" count={5} />;
}

export function AccountCardSkeleton() {
  return <LoadingSkeleton type="card" height="180px" />;
}

export function ChartSkeleton() {
  return <LoadingSkeleton type="chart" />;
}

export function ProfileSkeleton() {
  return (
    <div className="flex items-center space-x-4 p-4">
      <LoadingSkeleton type="image" className="rounded-full" height="64px" width="64px" />
      <div className="flex-1">
        <LoadingSkeleton type="text" count={2} />
      </div>
    </div>
  );
}