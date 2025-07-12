'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';

interface ThemeToggleProps {
  size?: 'sm' | 'md' | 'lg';
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ size = 'md' }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Check for saved theme preference or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme as 'light' | 'dark');
    document.documentElement.setAttribute('data-theme', savedTheme);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const sizeClasses = {
    sm: 'w-11 h-6',
    md: 'w-14 h-7',
    lg: 'w-16 h-8',
  };

  const knobSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const knobTranslate = {
    sm: theme === 'dark' ? 'translateX(20px)' : 'translateX(1px)',
    md: theme === 'dark' ? 'translateX(26px)' : 'translateX(1px)',
    lg: theme === 'dark' ? 'translateX(30px)' : 'translateX(1px)',
  };

  const iconSize = {
    sm: 12,
    md: 14,
    lg: 16,
  };

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative ${sizeClasses[size]} 
        rounded-full p-0.5
        transition-all duration-300
        bg-[rgba(var(--glass-rgb),0.3)]
        backdrop-blur-sm
        border-2 border-[var(--border-1)]
        hover:border-[var(--primary-blue)]
        focus:outline-none
        focus:ring-2
        focus:ring-[var(--primary-blue)]
        focus:ring-opacity-50
      `}
      aria-label="Toggle theme"
    >
      <motion.div
        className={`
          ${knobSizes[size]}
          rounded-full
          flex items-center justify-center
          bg-gradient-to-br from-[var(--primary-blue)] to-[var(--primary-indigo)]
          shadow-lg
        `}
        animate={{
          transform: knobTranslate[size],
        }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 30,
        }}
      >
        {theme === 'light' ? (
          <Sun size={iconSize[size]} className="text-white" />
        ) : (
          <Moon size={iconSize[size]} className="text-white" />
        )}
      </motion.div>
    </button>
  );
};

export default ThemeToggle;