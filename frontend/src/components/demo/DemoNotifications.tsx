import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, AlertCircle, Info, DollarSign } from 'lucide-react';
import { generateDemoNotifications, DemoNotification } from '@/utils/mockDataEnhancer';
import { useDemoMode } from '@/contexts/DemoModeContext';

export const DemoNotifications: React.FC = () => {
  const { isDemoMode } = useDemoMode();
  const [notifications, setNotifications] = useState<DemoNotification[]>([]);
  const [visibleNotifications, setVisibleNotifications] = useState<string[]>([]);

  useEffect(() => {
    if (isDemoMode) {
      const demoNotifications = generateDemoNotifications();
      setNotifications(demoNotifications);
      
      // Show notifications one by one with delay
      demoNotifications.forEach((notif, index) => {
        setTimeout(() => {
          setVisibleNotifications(prev => [...prev, notif.id]);
          
          // Auto-hide after 5 seconds
          setTimeout(() => {
            handleDismiss(notif.id);
          }, 5000);
        }, (index + 1) * 2000);
      });
    }
  }, [isDemoMode]);

  const handleDismiss = (id: string) => {
    setVisibleNotifications(prev => prev.filter(nId => nId !== id));
  };

  const getIcon = (type: DemoNotification['type']) => {
    switch (type) {
      case 'success':
        return <Check className="w-5 h-5" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5" />;
      case 'alert':
        return <AlertCircle className="w-5 h-5" />;
      case 'info':
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  const getColors = (type: DemoNotification['type']) => {
    switch (type) {
      case 'success':
        return {
          bg: 'bg-[var(--primary-emerald)]',
          text: 'text-white',
          border: 'border-[var(--primary-emerald)]',
        };
      case 'warning':
        return {
          bg: 'bg-[var(--primary-amber)]',
          text: 'text-white',
          border: 'border-[var(--primary-amber)]',
        };
      case 'alert':
        return {
          bg: 'bg-[var(--primary-red)]',
          text: 'text-white',
          border: 'border-[var(--primary-red)]',
        };
      case 'info':
      default:
        return {
          bg: 'bg-[var(--primary-blue)]',
          text: 'text-white',
          border: 'border-[var(--primary-blue)]',
        };
    }
  };

  if (!isDemoMode) return null;

  return (
    <div className="fixed top-20 right-4 z-50 space-y-3 max-w-sm">
      <AnimatePresence>
        {notifications
          .filter(notif => visibleNotifications.includes(notif.id))
          .map((notification) => {
            const colors = getColors(notification.type);
            
            return (
              <motion.div
                key={notification.id}
                initial={{ opacity: 0, x: 100, scale: 0.8 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 100, scale: 0.8 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                className={`
                  relative p-4 rounded-lg shadow-lg
                  bg-[rgba(var(--glass-rgb),var(--glass-alpha-high))] backdrop-blur-xl
                  border ${colors.border} border-opacity-20
                  overflow-hidden
                `}
              >
                {/* Background accent */}
                <div className={`absolute inset-0 ${colors.bg} opacity-10`} />
                
                {/* Content */}
                <div className="relative flex items-start gap-3">
                  <div className={`
                    p-2 rounded-lg ${colors.bg} ${colors.text}
                    flex-shrink-0
                  `}>
                    {getIcon(notification.type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-[var(--text-1)] text-sm">
                      {notification.title}
                    </h4>
                    <p className="text-xs text-[var(--text-2)] mt-1">
                      {notification.message}
                    </p>
                    
                    {notification.actionUrl && (
                      <button
                        onClick={() => {
                          window.location.href = notification.actionUrl!;
                          handleDismiss(notification.id);
                        }}
                        className={`
                          text-xs font-medium ${colors.bg} ${colors.text}
                          px-2 py-1 rounded mt-2
                          bg-opacity-20 hover:bg-opacity-30
                          transition-colors
                        `}
                      >
                        {notification.actionLabel || 'View'}
                      </button>
                    )}
                  </div>
                  
                  <button
                    onClick={() => handleDismiss(notification.id)}
                    className="p-1 rounded hover:bg-[rgba(var(--glass-rgb),0.1)] transition-colors"
                  >
                    <X className="w-4 h-4 text-[var(--text-2)]" />
                  </button>
                </div>
                
                {/* Progress bar for auto-dismiss */}
                <motion.div
                  className={`absolute bottom-0 left-0 h-1 ${colors.bg}`}
                  initial={{ width: '100%' }}
                  animate={{ width: '0%' }}
                  transition={{ duration: 5, ease: 'linear' }}
                />
              </motion.div>
            );
          })}
      </AnimatePresence>
    </div>
  );
};

// Toast notification for quick feedback
export const showToast = (
  message: string,
  type: 'success' | 'error' | 'info' = 'info',
  duration: number = 3000
) => {
  // Implementation would integrate with a toast library or custom solution
  console.log(`Toast: ${type} - ${message}`);
};

export default DemoNotifications;