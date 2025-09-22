import React, { useState, useRef, useEffect } from 'react';
import { motion, useMotionValue, useTransform, AnimatePresence } from 'framer-motion';
import { ChevronRight, CheckCircle, Lock } from 'lucide-react';
import { useSyntheticTracking } from '@/hooks/useSyntheticTracking';

interface SlideToConfirmProps {
  onConfirm: () => void;
  onCancel?: () => void;
  text?: string;
  confirmText?: string;
  amount?: number;
  recipient?: string;
  disabled?: boolean;
  className?: string;
  transactionType?: string;
  fromAccount?: string;
  toAccount?: string;
}

export const SlideToConfirmTracked: React.FC<SlideToConfirmProps> = ({
  onConfirm,
  onCancel,
  text = 'Slide to confirm',
  confirmText = 'Transaction confirmed!',
  amount,
  recipient,
  disabled = false,
  className = '',
  transactionType = 'transfer',
  fromAccount = 'default',
  toAccount,
}) => {
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [confirmationId] = useState(() => crypto.randomUUID());
  const constraintsRef = useRef<HTMLDivElement>(null);
  const sliderRef = useRef<HTMLDivElement>(null);
  
  const { trackSlideToConfirm } = useSyntheticTracking();
  
  const x = useMotionValue(0);
  const [sliderWidth, setSliderWidth] = useState(0);
  const [trackWidth, setTrackWidth] = useState(0);
  
  // Calculate dimensions
  useEffect(() => {
    if (constraintsRef.current && sliderRef.current) {
      const track = constraintsRef.current.offsetWidth;
      const slider = sliderRef.current.offsetWidth;
      setTrackWidth(track);
      setSliderWidth(slider);
    }
  }, []);
  
  const maxDrag = trackWidth - sliderWidth;
  
  // Transform values for visual feedback
  const progressBackground = useTransform(
    x,
    [0, maxDrag],
    ['0%', '100%']
  );
  
  const sliderOpacity = useTransform(
    x,
    [0, maxDrag * 0.8, maxDrag],
    [1, 0.8, 0.6]
  );
  
  const textOpacity = useTransform(
    x,
    [0, maxDrag * 0.5],
    [1, 0]
  );
  
  // Track drag progress
  useEffect(() => {
    const unsubscribe = x.onChange((latest) => {
      if (isDragging && maxDrag > 0) {
        const progress = latest / maxDrag;
        
        // Track progress at intervals (0%, 25%, 50%, 75%)
        const threshold = Math.floor(progress * 4) / 4;
        if (threshold > 0 && threshold < 1) {
          trackSlideToConfirm({
            transactionType,
            amount: amount || 0,
            fromAccount,
            toAccount,
            slideDistance: progress,
            confirmed: false,
            confirmationId
          });
        }
      }
    });
    
    return unsubscribe;
  }, [isDragging, maxDrag, trackSlideToConfirm, transactionType, amount, fromAccount, toAccount, confirmationId]);
  
  const handleDragEnd = async () => {
    setIsDragging(false);
    
    const finalProgress = x.get() / maxDrag;
    
    if (finalProgress >= 0.9) {
      // Snap to end and confirm
      x.set(maxDrag);
      setIsConfirmed(true);
      
      // Track completion
      await trackSlideToConfirm({
        transactionType,
        amount: amount || 0,
        fromAccount,
        toAccount,
        slideDistance: 1.0,
        confirmed: true,
        confirmationId
      });
      
      // Haptic feedback simulation
      if (navigator.vibrate) {
        navigator.vibrate([50, 30, 100]);
      }
      
      setTimeout(() => {
        onConfirm();
      }, 800);
    } else {
      // Track abandonment
      await trackSlideToConfirm({
        transactionType,
        amount: amount || 0,
        fromAccount,
        toAccount,
        slideDistance: finalProgress,
        confirmed: false,
        confirmationId
      });
      
      // Spring back to start
      x.set(0);
    }
  };
  
  const handleReset = () => {
    x.set(0);
    setIsConfirmed(false);
    onCancel?.();
  };

  return (
    <div className={`w-full max-w-md ${className}`}>
      {/* Transaction Details */}
      {(amount || recipient) && (
        <div className="mb-4 p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.2)] border border-[var(--border-1)]">
          {amount && (
            <p className="text-2xl font-bold text-[var(--text-1)] mb-1">
              ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          )}
          {recipient && (
            <p className="text-sm text-[var(--text-2)]">
              To: <span className="font-medium text-[var(--text-1)]">{recipient}</span>
            </p>
          )}
        </div>
      )}
      
      {/* Slider Track */}
      <div
        ref={constraintsRef}
        className={`
          relative h-16 rounded-full overflow-hidden
          bg-[rgba(var(--glass-rgb),0.2)]
          backdrop-blur-sm
          border border-[var(--glass-border)]
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-grab'}
          ${isDragging ? 'cursor-grabbing' : ''}
        `}
      >
        {/* Progress Background */}
        <motion.div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-[var(--primary-blue)] to-[var(--primary-emerald)] opacity-20"
          style={{ width: progressBackground }}
        />
        
        {/* Text */}
        <AnimatePresence mode="wait">
          {!isConfirmed ? (
            <motion.div
              key="slide-text"
              className="absolute inset-0 flex items-center justify-center pointer-events-none"
              style={{ opacity: textOpacity }}
            >
              <span className="text-[var(--text-1)] font-medium select-none">
                {text}
              </span>
            </motion.div>
          ) : (
            <motion.div
              key="confirm-text"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="absolute inset-0 flex items-center justify-center pointer-events-none"
            >
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-[var(--primary-emerald)]" />
                <span className="text-[var(--primary-emerald)] font-medium select-none">
                  {confirmText}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Slider Button */}
        <motion.div
          ref={sliderRef}
          className={`
            absolute top-1 left-1 bottom-1
            w-14 rounded-full
            bg-gradient-to-br from-[var(--primary-blue)] to-[var(--primary-indigo)]
            shadow-lg
            flex items-center justify-center
            ${isConfirmed ? 'pointer-events-none' : ''}
          `}
          style={{ x, opacity: sliderOpacity }}
          drag={!disabled && !isConfirmed ? "x" : false}
          dragConstraints={{ left: 0, right: maxDrag }}
          dragElastic={0}
          dragMomentum={false}
          onDragStart={() => setIsDragging(true)}
          onDragEnd={handleDragEnd}
          whileTap={{ scale: 0.95 }}
        >
          <AnimatePresence mode="wait">
            {!isConfirmed ? (
              <motion.div
                key="arrow"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center"
              >
                <ChevronRight className="w-5 h-5 text-white" />
                <ChevronRight className="w-5 h-5 text-white -ml-3" />
              </motion.div>
            ) : (
              <motion.div
                key="lock"
                initial={{ opacity: 0, rotate: 180 }}
                animate={{ opacity: 1, rotate: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Lock className="w-5 h-5 text-white" />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
        
        {/* Visual Feedback Particles */}
        {isDragging && (
          <motion.div
            className="absolute inset-y-0 left-0 pointer-events-none"
            style={{ width: progressBackground }}
          >
            {[...Array(3)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute top-1/2 w-1 h-1 rounded-full bg-[rgba(var(--glass-rgb),0.4)]"
                style={{ left: `${20 + i * 30}%` }}
                animate={{
                  y: [-8, 8, -8],
                  opacity: [0.3, 0.8, 0.3],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: i * 0.2,
                }}
              />
            ))}
          </motion.div>
        )}
      </div>
      
      {/* Cancel Button */}
      {isConfirmed && onCancel && (
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          onClick={handleReset}
          className="mt-4 w-full text-center text-sm text-[var(--text-2)] hover:text-[var(--text-1)] transition-colors"
        >
          Cancel Transaction
        </motion.button>
      )}
    </div>
  );
};

export default SlideToConfirmTracked;