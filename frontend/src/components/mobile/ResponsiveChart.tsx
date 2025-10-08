import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface ResponsiveChartProps {
  children: React.ReactNode;
  minHeight?: number;
  maxHeight?: number;
  aspectRatio?: number;
  className?: string;
  enablePinchZoom?: boolean;
}

export const ResponsiveChart: React.FC<ResponsiveChartProps> = ({
  children,
  minHeight = 200,
  maxHeight = 400,
  aspectRatio = 16 / 9,
  className = '',
  enablePinchZoom = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth;
        const calculatedHeight = width / aspectRatio;
        const height = Math.max(minHeight, Math.min(calculatedHeight, maxHeight));
        
        setDimensions({ width, height });
      }
    };

    updateDimensions();
    
    const resizeObserver = new ResizeObserver(updateDimensions);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [aspectRatio, minHeight, maxHeight]);

  const _handlePinch = (e: TouchEvent) => {
    if (!enablePinchZoom || e.touches.length !== 2) return;

    const touch1 = e.touches[0];
    const touch2 = e.touches[1];
    const _distance = Math.sqrt(
      Math.pow(touch2.clientX - touch1.clientX, 2) +
      Math.pow(touch2.clientY - touch1.clientY, 2)
    );

    // Implementation of pinch zoom would go here
    // This is a simplified version
  };

  const handleDoubleTap = () => {
    setScale(scale === 1 ? 1.5 : 1);
    setPosition({ x: 0, y: 0 });
  };

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden touch-manipulation ${className}`}
      style={{ height: dimensions.height || minHeight }}
      onDoubleClick={handleDoubleTap}
    >
      <motion.div
        animate={{
          scale,
          x: position.x,
          y: position.y,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="w-full h-full"
      >
        {/* Chart container with responsive wrapper */}
        <div className="w-full h-full">
          {React.Children.map(children, child => {
            if (React.isValidElement(child)) {
              return React.cloneElement(child as React.ReactElement<any>, {
                width: dimensions.width,
                height: dimensions.height,
              });
            }
            return child;
          })}
        </div>
      </motion.div>

      {/* Zoom controls for mobile */}
      {enablePinchZoom && (
        <div className="absolute bottom-2 right-2 flex gap-2 md:hidden">
          <button
            onClick={() => setScale(Math.min(scale + 0.2, 2))}
            className="w-8 h-8 rounded-full bg-[rgba(var(--glass-rgb),0.8)] backdrop-blur-sm border border-[var(--glass-border)] flex items-center justify-center text-sm touch-target"
          >
            +
          </button>
          <button
            onClick={() => setScale(Math.max(scale - 0.2, 0.8))}
            className="w-8 h-8 rounded-full bg-[rgba(var(--glass-rgb),0.8)] backdrop-blur-sm border border-[var(--glass-border)] flex items-center justify-center text-sm touch-target"
          >
            -
          </button>
        </div>
      )}
    </div>
  );
};

// Mobile-optimized legend component
export const MobileLegend: React.FC<{
  items: Array<{
    label: string;
    color: string;
    value?: string | number;
  }>;
  columns?: number;
}> = ({ items, columns = 2 }) => {
  return (
    <div className={`grid grid-cols-${columns} gap-2 mt-4`}>
      {items.map((item, index) => (
        <div key={index} className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: item.color }}
          />
          <div className="flex-1 min-w-0">
            <span className="text-xs text-[var(--text-2)] truncate block">
              {item.label}
            </span>
            {item.value !== undefined && (
              <span className="text-xs font-medium text-[var(--text-1)]">
                {item.value}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ResponsiveChart;