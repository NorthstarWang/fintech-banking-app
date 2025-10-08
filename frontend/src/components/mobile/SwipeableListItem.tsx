import React, { useRef, useState } from 'react';
import { motion, useAnimation, PanInfo } from 'framer-motion';
import { Trash2, Edit, Star, Archive } from 'lucide-react';

interface SwipeAction {
  icon: React.ReactNode;
  label: string;
  color: string;
  action: () => void;
}

interface SwipeableListItemProps {
  children: React.ReactNode;
  leftActions?: SwipeAction[];
  rightActions?: SwipeAction[];
  onSwipeComplete?: (direction: 'left' | 'right') => void;
  className?: string;
  threshold?: number;
}

export const SwipeableListItem: React.FC<SwipeableListItemProps> = ({
  children,
  leftActions = [],
  rightActions = [],
  onSwipeComplete,
  className = '',
  threshold = 100,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const controls = useAnimation();
  const constraintsRef = useRef<HTMLDivElement>(null);

  const handleDragStart = () => {
    setIsDragging(true);
    // Haptic feedback
    if ('vibrate' in navigator) {
      navigator.vibrate(10);
    }
  };

  const handleDragEnd = (event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    setIsDragging(false);
    const { offset, velocity } = info;
    
    // Determine if swipe is strong enough
    if (Math.abs(offset.x) > threshold || Math.abs(velocity.x) > 500) {
      const direction = offset.x > 0 ? 'right' : 'left';
      const actions = direction === 'right' ? leftActions : rightActions;
      
      if (actions.length > 0) {
        // Haptic feedback for action trigger
        if ('vibrate' in navigator) {
          navigator.vibrate([20, 10, 20]);
        }
        
        // Animate out
        controls.start({
          x: direction === 'right' ? 400 : -400,
          opacity: 0,
          transition: { duration: 0.3 }
        }).then(() => {
          onSwipeComplete?.(direction);
          // Execute the primary action
          actions[0]?.action();
        });
      } else {
        // Spring back if no actions
        controls.start({ x: 0 });
      }
    } else {
      // Spring back
      controls.start({ x: 0 });
    }
  };

  const _getBackgroundGradient = (x: number) => {
    if (x > 0 && leftActions.length > 0) {
      const progress = Math.min(x / threshold, 1);
      return `linear-gradient(to right, ${leftActions[0].color}${Math.floor(progress * 255).toString(16).padStart(2, '0')}, transparent)`;
    } else if (x < 0 && rightActions.length > 0) {
      const progress = Math.min(Math.abs(x) / threshold, 1);
      return `linear-gradient(to left, ${rightActions[0].color}${Math.floor(progress * 255).toString(16).padStart(2, '0')}, transparent)`;
    }
    return 'transparent';
  };

  return (
    <div ref={constraintsRef} className={`relative overflow-hidden ${className}`}>
      {/* Action indicators */}
      <div className="absolute inset-0 flex items-center justify-between px-4 pointer-events-none">
        {/* Left actions */}
        {leftActions.length > 0 && (
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ 
              opacity: isDragging ? 1 : 0, 
              scale: isDragging ? 1 : 0.8 
            }}
          >
            {leftActions.map((action, index) => (
              <div
                key={index}
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: action.color }}
              >
                {action.icon}
              </div>
            ))}
          </motion.div>
        )}

        {/* Right actions */}
        {rightActions.length > 0 && (
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ 
              opacity: isDragging ? 1 : 0, 
              scale: isDragging ? 1 : 0.8 
            }}
          >
            {rightActions.map((action, index) => (
              <div
                key={index}
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: action.color }}
              >
                {action.icon}
              </div>
            ))}
          </motion.div>
        )}
      </div>

      {/* Swipeable content */}
      <motion.div
        drag="x"
        dragElastic={0.2}
        dragConstraints={{ left: rightActions.length > 0 ? -200 : 0, right: leftActions.length > 0 ? 200 : 0 }}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        animate={controls}
        whileTap={{ scale: 0.98 }}
        style={{
          touchAction: 'pan-y',
        }}
        className="relative glass-card cursor-grab active:cursor-grabbing"
      >
        {children}
      </motion.div>
    </div>
  );
};

// Preset swipe actions
export const SWIPE_ACTIONS = {
  delete: (onDelete: () => void): SwipeAction => ({
    icon: <Trash2 className="w-5 h-5 text-white" />,
    label: 'Delete',
    color: 'var(--primary-red)',
    action: onDelete,
  }),
  edit: (onEdit: () => void): SwipeAction => ({
    icon: <Edit className="w-5 h-5 text-white" />,
    label: 'Edit',
    color: 'var(--primary-blue)',
    action: onEdit,
  }),
  favorite: (onFavorite: () => void): SwipeAction => ({
    icon: <Star className="w-5 h-5 text-white" />,
    label: 'Favorite',
    color: 'var(--primary-amber)',
    action: onFavorite,
  }),
  archive: (onArchive: () => void): SwipeAction => ({
    icon: <Archive className="w-5 h-5 text-white" />,
    label: 'Archive',
    color: 'var(--text-2)',
    action: onArchive,
  }),
};

export default SwipeableListItem;