'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import { useRouter } from 'next/navigation';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    // Log the error to console in development
    if (process.env.NODE_ENV === 'development') {
    }
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--bg-color)]">
      {/* Background gradient */}
      <div className="fixed inset-0 -z-10">
        <div 
          className="absolute inset-0 bg-gradient-to-br from-[var(--primary-red)] via-[var(--primary-pink)] to-[var(--primary-amber)] opacity-5"
          style={{
            backgroundSize: '400% 400%',
            animation: 'gradient-animation 30s ease infinite',
          }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <Card variant="error" className="p-8">
          <div className="flex flex-col items-center text-center">
            {/* Error Icon */}
            <div className="p-4 rounded-full bg-[rgba(var(--primary-red),0.1)] mb-6">
              <AlertCircle size={48} className="text-[var(--primary-red)]" />
            </div>

            {/* Error Title */}
            <h1 className="text-2xl font-bold text-[var(--text-1)] mb-2">
              Oops! Something went wrong
            </h1>

            {/* Error Description */}
            <p className="text-[var(--text-2)] mb-6">
              We encountered an unexpected error. Don&apos;t worry, your data is safe.
            </p>

            {/* Error Details (Development Only) */}
            {process.env.NODE_ENV === 'development' && error.message && (
              <div className="w-full mb-6">
                <Card variant="subtle" className="p-4 text-left">
                  <h3 className="text-sm font-semibold text-[var(--text-1)] mb-2">
                    Error Details (Development Only)
                  </h3>
                  <p className="text-xs text-[var(--text-2)] font-mono break-all">
                    {error.message}
                  </p>
                  {error.digest && (
                    <p className="text-xs text-[var(--text-2)] mt-2">
                      Error ID: {error.digest}
                    </p>
                  )}
                </Card>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 w-full">
              <Button
                variant="secondary"
                onClick={() => router.push('/dashboard')}
                icon={<Home size={18} />}
                fullWidth
              >
                Go Home
              </Button>
              <Button
                variant="primary"
                onClick={reset}
                icon={<RefreshCw size={18} />}
                fullWidth
              >
                Try Again
              </Button>
            </div>
          </div>
        </Card>

        {/* Additional Help Text */}
        <p className="text-center text-sm text-[var(--text-2)] mt-6">
          If this problem persists, please contact support or try refreshing the page.
        </p>
      </motion.div>
    </div>
  );
}