'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Home, 
  ArrowLeft, 
  Compass,
  MapPin,
  AlertTriangle,
  Sparkles
} from 'lucide-react';
import Button from '@/components/ui/Button';
import AnimatedLogo from '@/components/ui/AnimatedLogo';
import ThemeToggle from '@/components/ui/ThemeToggle';

export default function NotFound() {
  const router = useRouter();
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth - 0.5) * 20,
        y: (e.clientY / window.innerHeight - 0.5) * 20,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

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

  const floatingVariants = {
    initial: { y: 0, rotate: 0 },
    animate: {
      y: [-20, 20, -20],
      rotate: [0, 5, -5, 0],
      transition: {
        duration: 6,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  };

  const numberVariants = {
    initial: { scale: 1, rotate: 0 },
    hover: {
      scale: [1, 1.2, 1.1],
      rotate: [0, 10, -10, 0],
      transition: {
        duration: 0.5,
      },
    },
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>
      {/* Animated background elements */}
      <motion.div
        className="absolute top-1/4 -left-20 w-72 h-72 rounded-full"
        style={{
          background: 'radial-gradient(circle, var(--vibrant-blue) 0%, transparent 70%)',
          filter: 'blur(80px)',
          x: mousePosition.x,
          y: mousePosition.y,
        }}
        animate={{
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      
      <motion.div
        className="absolute bottom-1/4 -right-20 w-96 h-96 rounded-full"
        style={{
          background: 'radial-gradient(circle, var(--vibrant-emerald) 0%, transparent 70%)',
          filter: 'blur(100px)',
          x: -mousePosition.x,
          y: -mousePosition.y,
        }}
        animate={{
          scale: [1, 1.3, 1],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      {/* Floating elements */}
      <motion.div
        className="absolute top-20 right-1/4"
        variants={floatingVariants}
        initial="initial"
        animate="animate"
      >
        <Compass className="w-12 h-12 text-[var(--primary-blue)] opacity-20" />
      </motion.div>

      <motion.div
        className="absolute bottom-32 left-1/3"
        variants={floatingVariants}
        initial="initial"
        animate="animate"
        style={{ animationDelay: '2s' }}
      >
        <MapPin className="w-10 h-10 text-[var(--primary-emerald)] opacity-20" />
      </motion.div>

      <motion.div
        className="absolute top-1/3 left-20"
        animate={{
          rotate: 360,
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'linear',
        }}
      >
        <Search className="w-8 h-8 text-[var(--primary-indigo)] opacity-20" />
      </motion.div>

      <motion.div
        className="glass-card relative z-10 max-w-2xl w-full mx-4 p-8 md:p-12 text-center overflow-hidden"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Animated border gradient */}
        <motion.div
          className="absolute inset-0 rounded-2xl"
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
          {/* Logo */}
          <motion.div
            variants={itemVariants}
            className="mb-8 flex justify-center"
          >
            <AnimatedLogo size="lg" showText={false} />
          </motion.div>

          {/* 404 Number Animation */}
          <motion.div
            variants={itemVariants}
            className="mb-8 flex justify-center items-center gap-4"
          >
            <motion.div
              className="relative"
              variants={numberVariants}
              initial="initial"
              whileHover="hover"
            >
              <span className="text-8xl md:text-9xl font-bold gradient-text">4</span>
              <motion.div
                className="absolute -top-2 -right-2"
                animate={{
                  rotate: [0, 360],
                  scale: [1, 1.2, 1],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                <Sparkles className="w-6 h-6 text-[var(--primary-amber)]" />
              </motion.div>
            </motion.div>

            <motion.div
              className="relative"
              animate={{
                rotate: [0, 360],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: 'linear',
              }}
            >
              <div className="w-20 h-20 md:w-24 md:h-24 rounded-full border-4 border-[var(--primary-emerald)] border-dashed flex items-center justify-center">
                <AlertTriangle className="w-10 h-10 md:w-12 md:h-12 text-[var(--primary-amber)]" />
              </div>
            </motion.div>

            <motion.div
              className="relative"
              variants={numberVariants}
              initial="initial"
              whileHover="hover"
            >
              <span className="text-8xl md:text-9xl font-bold gradient-text">4</span>
              <motion.div
                className="absolute -bottom-2 -left-2"
                animate={{
                  y: [0, -10, 0],
                  x: [0, 5, 0],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                <Search className="w-8 h-8 text-[var(--primary-blue)]" />
              </motion.div>
            </motion.div>
          </motion.div>

          {/* Title */}
          <motion.h1
            variants={itemVariants}
            className="text-3xl md:text-4xl font-bold gradient-text mb-4"
          >
            Page Not Found
          </motion.h1>

          {/* Description */}
          <motion.p
            variants={itemVariants}
            className="text-lg text-[var(--text-2)] mb-8 max-w-md mx-auto"
          >
            Looks like you&apos;ve wandered into uncharted territory. The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </motion.p>

          {/* Lost items animation */}
          <motion.div
            variants={itemVariants}
            className="flex items-center justify-center gap-6 mb-8"
          >
            <motion.div
              className="p-3 rounded-full bg-[rgba(var(--primary-blue),0.1)]"
              animate={{
                scale: [1, 1.1, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              <Compass className="w-8 h-8 text-[var(--primary-blue)]" />
            </motion.div>
            
            <motion.div
              className="p-3 rounded-full bg-[rgba(var(--primary-emerald),0.1)]"
              animate={{
                scale: [1, 1.1, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 0.5,
              }}
            >
              <MapPin className="w-8 h-8 text-[var(--primary-emerald)]" />
            </motion.div>
            
            <motion.div
              className="p-3 rounded-full bg-[rgba(var(--primary-indigo),0.1)]"
              animate={{
                scale: [1, 1.1, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 1,
              }}
            >
              <Search className="w-8 h-8 text-[var(--primary-indigo)]" />
            </motion.div>
          </motion.div>

          {/* Action buttons */}
          <motion.div
            variants={itemVariants}
            className="space-y-3"
          >
            <Button
              variant="primary"
              fullWidth
              onClick={() => router.push('/dashboard')}
              icon={<Home size={18} />}
              className="group"
            >
              <span>Go to Dashboard</span>
              <motion.span
                className="inline-block ml-2"
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
              variant="secondary"
              fullWidth
              onClick={() => router.back()}
              icon={<ArrowLeft size={18} />}
            >
              Go Back
            </Button>
          </motion.div>

          {/* Fun message */}
          <motion.p
            variants={itemVariants}
            className="mt-8 text-sm text-[var(--text-2)] opacity-60"
          >
            <AnimatePresence mode="wait">
              <motion.span
                key="message"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
              >
                Error code: 404 | Don&apos;t worry, even the best explorers get lost sometimes! 🧭
              </motion.span>
            </AnimatePresence>
          </motion.p>
        </div>
      </motion.div>

      {/* Additional decorative elements */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 right-1/3 w-2 h-2 bg-[var(--primary-blue)] rounded-full opacity-50" />
        <div className="absolute bottom-1/3 left-1/4 w-3 h-3 bg-[var(--primary-emerald)] rounded-full opacity-40" />
        <div className="absolute top-1/2 right-1/4 w-2 h-2 bg-[var(--primary-indigo)] rounded-full opacity-60" />
      </div>
    </div>
  );
}