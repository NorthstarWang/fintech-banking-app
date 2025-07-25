import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AnimatedCardNumberProps {
  showNumbers: boolean;
  fullNumber: string;
  lastFourDigits: string;
  className?: string;
}

export const AnimatedCardNumber: React.FC<AnimatedCardNumberProps> = ({
  showNumbers,
  fullNumber,
  lastFourDigits,
  className = ''
}) => {
  const maskedNumber = `**** **** **** ${lastFourDigits}`;
  
  return (
    <div className={`relative ${className}`}>
      <AnimatePresence mode="wait">
        {showNumbers ? (
          <motion.p
            key="full"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="font-mono"
          >
            {fullNumber}
          </motion.p>
        ) : (
          <motion.p
            key="masked"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="font-mono"
          >
            {maskedNumber}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
};

interface AnimatedCVVProps {
  showNumbers: boolean;
  cvv: string;
  className?: string;
}

export const AnimatedCVV: React.FC<AnimatedCVVProps> = ({
  showNumbers,
  cvv,
  className = ''
}) => {
  return (
    <div className={`relative ${className}`}>
      <AnimatePresence mode="wait">
        {showNumbers ? (
          <motion.p
            key="full-cvv"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="font-mono"
          >
            {cvv}
          </motion.p>
        ) : (
          <motion.p
            key="masked-cvv"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="font-mono"
          >
            ***
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
};