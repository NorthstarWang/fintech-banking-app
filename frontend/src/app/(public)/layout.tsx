'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import ErrorBoundary from '@/components/analytics/ErrorBoundary';
import BackgroundEffects from '@/components/ui/BackgroundEffects';

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Redirect authenticated users to dashboard
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--primary-blue)] mx-auto"></div>
          <p className="mt-4 text-[var(--text-2)]">Loading...</p>
        </div>
      </div>
    );
  }

  // Only render if not authenticated
  if (isAuthenticated) {
    return null;
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen relative">
        <BackgroundEffects />
        {children}
      </div>
    </ErrorBoundary>
  );
}