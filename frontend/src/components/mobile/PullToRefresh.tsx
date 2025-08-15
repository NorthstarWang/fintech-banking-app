import React, { useEffect, useRef, useState } from 'react';
import { motion, useAnimation, AnimatePresence } from 'framer-motion';
import { RefreshCw } from 'lucide-react';

interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => Promise<void>;
  disabled?: boolean;
  threshold?: number;
  refreshComponent?: React.ReactNode;
  className?: string;
}

export const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  disabled = false,
  threshold = 80,
  refreshComponent,
  className = '',
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [shouldRefresh, setShouldRefresh] = useState(false);
  
  const startY = useRef<number | null>(null);
  const controls = useAnimation();
  const containerRef = useRef<HTMLDivElement>(null);

  const handleTouchStart = (e: TouchEvent) => {
    if (disabled || isRefreshing) return;
    
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    if (scrollTop > 0) return;
    
    startY.current = e.touches[0].clientY;
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (!startY.current || disabled || isRefreshing) return;
    
    const currentY = e.touches[0].clientY;
    const distance = currentY - startY.current;
    
    if (distance > 0) {
      e.preventDefault();
      const adjustedDistance = Math.min(distance * 0.5, threshold * 1.5);
      setPullDistance(adjustedDistance);
      
      if (adjustedDistance >= threshold) {
        setShouldRefresh(true);
        // Haptic feedback (will only work on supported devices)
        if ('vibrate' in navigator) {
          navigator.vibrate(10);
        }
      } else {
        setShouldRefresh(false);
      }
    }
  };

  const handleTouchEnd = async () => {
    if (!startY.current || disabled || isRefreshing) return;
    
    startY.current = null;
    
    if (shouldRefresh && pullDistance >= threshold) {
      setIsRefreshing(true);
      setShouldRefresh(false);
      
      // Haptic feedback for refresh start
      if ('vibrate' in navigator) {
        navigator.vibrate([20, 10, 20]);
      }
      
      await controls.start({
        y: threshold,
        transition: { type: 'spring', stiffness: 200, damping: 20 }
      });
      
      try {
        await onRefresh();
      } catch (error) {
        console.error('Refresh failed:', error);
      } finally {
        setIsRefreshing(false);
        setPullDistance(0);
        await controls.start({
          y: 0,
          transition: { type: 'spring', stiffness: 200, damping: 20 }
        });
      }
    } else {
      setPullDistance(0);
      await controls.start({
        y: 0,
        transition: { type: 'spring', stiffness: 200, damping: 20 }
      });
    }
  };

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('touchstart', handleTouchStart, { passive: true });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchmove', handleTouchMove);
      container.removeEventListener('touchend', handleTouchEnd);
    };
  }, [disabled, isRefreshing, threshold]);

  useEffect(() => {
    if (!isRefreshing && pullDistance === 0) {
      controls.set({ y: 0 });
    } else if (!isRefreshing) {
      controls.set({ y: pullDistance });
    }
  }, [pullDistance, isRefreshing, controls]);

  const rotation = (pullDistance / threshold) * 360;
  const scale = Math.min(pullDistance / threshold, 1);
  const opacity = Math.min(pullDistance / threshold, 1);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Pull indicator */}
      <AnimatePresence>
        {(pullDistance > 0 || isRefreshing) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute top-0 left-0 right-0 flex justify-center pointer-events-none z-50"
            style={{ marginTop: '-60px' }}
          >
            <motion.div
              animate={{ y: pullDistance + 60 }}
              className="flex items-center justify-center"
            >
              {refreshComponent || (
                <motion.div
                  className="w-10 h-10 rounded-full bg-[var(--primary-blue)] shadow-lg flex items-center justify-center"
                  animate={{
                    scale: isRefreshing ? [1, 1.1, 1] : scale,
                    opacity,
                  }}
                  transition={isRefreshing ? {
                    scale: { repeat: Infinity, duration: 1 }
                  } : {}}
                >
                  <motion.div
                    animate={{
                      rotate: isRefreshing ? 360 : rotation,
                    }}
                    transition={isRefreshing ? {
                      rotate: { repeat: Infinity, duration: 1, ease: 'linear' }
                    } : {}}
                  >
                    <RefreshCw 
                      className="w-5 h-5 text-white" 
                      strokeWidth={2.5}
                    />
                  </motion.div>
                </motion.div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Content */}
      <motion.div animate={controls}>
        {children}
      </motion.div>
    </div>
  );
};

export default PullToRefresh;