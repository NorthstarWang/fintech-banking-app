'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, AlertCircle, ArrowRight, Shield } from 'lucide-react';
import Button from '@/components/ui/Button';
import AnimatedLogo from '@/components/ui/AnimatedLogo';
import ThemeToggle from '@/components/ui/ThemeToggle';
import BackgroundEffects from '@/components/ui/BackgroundEffects';

export default function SessionTimeoutPage() {
  const router = useRouter();
  const [countdown, setCountdown] = useState(10);
  const [isRedirecting, setIsRedirecting] = useState(false);

  // Clear all auth data on mount
  useEffect(() => {
    // Clear everything immediately
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
      localStorage.removeItem('currentUser');
      // Clear cookie multiple ways to ensure it's gone
      document.cookie = 'authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict';
      document.cookie = 'authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'authToken=; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    }
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          setIsRedirecting(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Separate effect for navigation
  useEffect(() => {
    if (countdown === 0 && isRedirecting) {
      router.push('/');
    }
  }, [countdown, isRedirecting, router]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 100,
        damping: 10,
      },
    },
  };

  const pulseVariants = {
    initial: { scale: 1, opacity: 0.5 },
    animate: {
      scale: [1, 1.2, 1],
      opacity: [0.5, 0.8, 0.5],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  };

  const floatingVariants = {
    initial: { y: 0 },
    animate: {
      y: [-10, 10, -10],
      transition: {
        duration: 4,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Background Effects */}
      <BackgroundEffects />
      
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      <motion.div
        className="glass-card relative z-10 max-w-md w-full mx-4 p-8 text-center overflow-hidden"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Animated border gradient */}
        <motion.div
          className="absolute inset-0 rounded-2xl overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, var(--primary-blue), var(--primary-emerald), var(--primary-indigo), var(--primary-blue))',
            padding: '2px',
            backgroundSize: '300% 300%',
          }}
          animate={{
            backgroundPosition: ['0% 0%', '100% 100%', '0% 0%'],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'linear',
          }}
        >
          <div className="absolute inset-[2px] bg-[var(--bg-color)] rounded-2xl" />
        </motion.div>

        <div className="relative z-10">
          {/* Logo with floating animation */}
          <motion.div
            variants={itemVariants}
            className="mb-6 flex justify-center"
          >
            <motion.div
              variants={floatingVariants}
              initial="initial"
              animate="animate"
            >
              <AnimatedLogo size="lg" showText={false} />
            </motion.div>
          </motion.div>

          {/* Alert icon with pulse */}
          <motion.div
            variants={itemVariants}
            className="mb-6 flex justify-center"
          >
            <div className="relative">
              <motion.div
                className="absolute inset-0 bg-[var(--primary-amber)] rounded-full"
                variants={pulseVariants}
                initial="initial"
                animate="animate"
              />
              <div className="relative bg-[rgba(var(--primary-amber),0.2)] p-4 rounded-full">
                <Clock className="w-12 h-12 text-[var(--primary-amber)]" />
              </div>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            variants={itemVariants}
            className="text-3xl font-bold gradient-text mb-4"
          >
            Session Expired
          </motion.h1>

          {/* Description */}
          <motion.p
            variants={itemVariants}
            className="text-[var(--text-2)] mb-8"
          >
            Your session has timed out for security reasons. Please log in again to continue managing your finances.
          </motion.p>

          {/* Security notice */}
          <motion.div
            variants={itemVariants}
            className="flex items-center gap-3 p-4 rounded-xl bg-[rgba(var(--glass-rgb),0.3)] border border-[var(--glass-border)] mb-8"
          >
            <Shield className="w-5 h-5 text-[var(--primary-emerald)] flex-shrink-0" />
            <p className="text-sm text-[var(--text-2)] text-left">
              We automatically log you out after a period of inactivity to protect your financial information.
            </p>
          </motion.div>

          {/* Countdown */}
          <AnimatePresence mode="wait">
            {!isRedirecting && (
              <motion.div
                key={countdown}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.2 }}
                className="mb-8"
              >
                <p className="text-sm text-[var(--text-2)] mb-2">
                  Redirecting to home in
                </p>
                <motion.div
                  className="text-4xl font-bold gradient-text"
                  animate={{
                    scale: [1, 1.1, 1],
                  }}
                  transition={{
                    duration: 0.3,
                  }}
                >
                  {countdown}
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action buttons */}
          <motion.div
            variants={itemVariants}
            className="space-y-3"
          >
            <Button
              variant="primary"
              fullWidth
              onClick={() => router.push('/')}
              icon={<ArrowRight size={18} />}
              className="group"
            >
              <span>Return to Login</span>
              <motion.span
                className="inline-block ml-1"
                animate={{
                  x: [0, 5, 0],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                →
              </motion.span>
            </Button>

            <Button
              variant="ghost"
              fullWidth
              onClick={() => router.push('/')}
            >
              Go to Homepage
            </Button>
          </motion.div>

          {/* Loading indicator when redirecting */}
          <AnimatePresence>
            {isRedirecting && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex items-center justify-center bg-[var(--bg-color)] bg-opacity-90 rounded-2xl"
              >
                <div className="flex flex-col items-center gap-4">
                  <motion.div
                    className="w-16 h-16 border-4 border-[var(--primary-blue)] border-t-transparent rounded-full"
                    animate={{
                      rotate: 360,
                    }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: 'linear',
                    }}
                  />
                  <p className="text-[var(--text-2)]">Redirecting...</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Additional floating elements */}
      <motion.div
        className="absolute top-1/4 right-1/4 z-0"
        animate={{
          rotate: 360,
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'linear',
        }}
      >
        <AlertCircle className="w-8 h-8 text-[var(--primary-amber)] opacity-30" />
      </motion.div>

      <motion.div
        className="absolute bottom-1/3 left-1/4 z-0"
        animate={{
          rotate: -360,
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'linear',
        }}
      >
        <Clock className="w-6 h-6 text-[var(--primary-blue)] opacity-30" />
      </motion.div>
    </div>
  );
}