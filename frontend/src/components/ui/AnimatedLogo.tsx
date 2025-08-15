import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, DollarSign, BarChart3 } from 'lucide-react';

interface AnimatedLogoProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
}

export const AnimatedLogo: React.FC<AnimatedLogoProps> = ({
  variant = 'primary',
  size = 'md',
  showText = true,
}) => {
  const sizeMap = {
    sm: { icon: 24, text: 'text-lg' },
    md: { icon: 32, text: 'text-2xl' },
    lg: { icon: 48, text: 'text-3xl' },
    xl: { icon: 64, text: 'text-4xl' },
  };

  const currentSize = sizeMap[size];

  const containerVariants = {
    initial: { opacity: 0, scale: 0.8 },
    animate: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.5,
        staggerChildren: 0.1,
      },
    },
  };

  const iconVariants = {
    initial: { opacity: 0, y: 20 },
    animate: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: 'easeOut',
      },
    },
  };

  const floatAnimation = {
    animate: {
      y: [-2, 2, -2],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  };

  return (
    <motion.div
      className="flex items-center gap-3"
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      <div className="relative">
        {/* Background glow */}
        <motion.div
          className="absolute inset-0 rounded-full opacity-30"
          style={{
            background: variant === 'primary'
              ? 'radial-gradient(circle, var(--vibrant-blue) 0%, transparent 70%)'
              : 'radial-gradient(circle, var(--vibrant-emerald) 0%, transparent 70%)',
            filter: 'blur(20px)',
          }}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />

        {/* Logo icon container */}
        <motion.div
          className={`
            relative
            w-${currentSize.icon}
            h-${currentSize.icon}
            rounded-xl
            ${variant === 'primary' ? 'gradient-main' : 'gradient-accent'}
            shadow-lg
            flex items-center justify-center
          `}
          style={{ width: currentSize.icon, height: currentSize.icon }}
          variants={floatAnimation}
          animate="animate"
        >
          {/* Animated icons */}
          <motion.div
            className="absolute"
            variants={iconVariants}
            animate={{
              rotate: [0, 10, -10, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            <TrendingUp
              size={currentSize.icon * 0.5}
              className="text-white"
              strokeWidth={2.5}
            />
          </motion.div>
          
          <motion.div
            className="absolute"
            variants={iconVariants}
            animate={{
              opacity: [0.3, 1, 0.3],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: 0.5,
            }}
          >
            <DollarSign
              size={currentSize.icon * 0.3}
              className="text-white/80"
              style={{
                transform: 'translate(-8px, -8px)',
              }}
            />
          </motion.div>
        </motion.div>
      </div>

      {showText && (
        <motion.div
          className="flex flex-col"
          variants={iconVariants}
        >
          <h1 className={`${currentSize.text} font-bold gradient-text`}>
            FinanceHub
          </h1>
          <p className="text-xs text-[var(--text-2)] -mt-1">
            Smart Banking Solutions
          </p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default AnimatedLogo;