'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSessionManager } from '@/utils/SessionManager';
import { useSecurity } from '@/contexts/SecurityContext';
import Button from '@/components/ui/Button';
import Portal from '@/components/ui/Portal';

export default function SessionTimeoutModal() {
  const { isActive, showWarning, getFormattedTime, extend, reset } = useSessionManager();
  const { config } = useSecurity();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(showWarning && isActive);
  }, [showWarning, isActive]);

  const handleExtend = () => {
    extend(config.sessionTimeout * 60 * 1000); // Extend by full session time
    setIsVisible(false);
  };

  const handleContinue = () => {
    reset();
    setIsVisible(false);
  };

  return (
    <Portal>
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--bg-overlay)] backdrop-blur-sm p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[rgba(var(--glass-rgb),var(--glass-alpha-high))] backdrop-blur-2xl rounded-xl shadow-2xl border border-[var(--glass-border-prominent)] max-w-md w-full p-6"
            >
            <div className="text-center">
              <div className="mb-4">
                <svg
                  className="mx-auto h-12 w-12 text-[var(--primary-amber)]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>

              <h3 className="text-xl font-semibold text-[var(--text-1)] mb-2">
                Session Expiring Soon
              </h3>

              <p className="text-[var(--text-2)] mb-6">
                Your session will expire in{' '}
                <span className="font-semibold text-[var(--primary-red)]">
                  {getFormattedTime()}
                </span>
                . Would you like to continue?
              </p>

              <div className="flex gap-3 justify-center">
                <Button
                  onClick={handleContinue}
                  className="flex-1"
                >
                  Continue Session
                </Button>
                <Button
                  onClick={() => window.location.href = '/logout'}
                  variant="secondary"
                  className="flex-1"
                >
                  Logout
                </Button>
              </div>
            </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Portal>
  );
}

// Auto-logout component
export function AutoLogoutHandler() {
  const { isActive } = useSessionManager();
  const [hasLoggedOut, setHasLoggedOut] = useState(false);

  useEffect(() => {
    if (!isActive && !hasLoggedOut) {
      setHasLoggedOut(true);
      // Perform logout
      window.location.href = '/session-timeout';
    }
  }, [isActive, hasLoggedOut]);

  return null;
}