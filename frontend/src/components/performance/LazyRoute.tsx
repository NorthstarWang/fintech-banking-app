'use client';

import { lazy, Suspense, ComponentType } from 'react';
import LoadingSkeleton from './LoadingSkeleton';

interface LazyRouteProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  loader: () => Promise<{ default: ComponentType<any> }>;
  loadingComponent?: React.ReactNode;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

export function LazyRoute({ 
  loader, 
  loadingComponent = <LoadingSkeleton type="page" />,
  ...props 
}: LazyRouteProps) {
  const Component = lazy(loader);

  return (
    <Suspense fallback={loadingComponent}>
      <Component {...props} />
    </Suspense>
  );
}

// Helper function to create lazy-loaded components with error boundary
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function createLazyComponent<T extends ComponentType<any>>(
  loader: () => Promise<{ default: T }>,
  options?: {
    loadingComponent?: React.ReactNode;
    errorFallback?: React.ReactNode;
  }
): React.FC<React.ComponentProps<T>> {
  const LazyComponent = lazy(loader);
  
  const LazyRouteComponent = (props: React.ComponentProps<T>) => (
    <Suspense fallback={options?.loadingComponent || <LoadingSkeleton type="component" />}>
      <LazyComponent {...props} />
    </Suspense>
  );

  LazyRouteComponent.displayName = 'LazyRouteComponent';
  return LazyRouteComponent;
}

// Route configuration for lazy loading
export const lazyRoutes = {
  dashboard: () => import('@/app/(authenticated)/dashboard/page'),
  accounts: () => import('@/app/(authenticated)/accounts/page'),
  transactions: () => import('@/app/(authenticated)/transactions/page'),
  budget: () => import('@/app/(authenticated)/budget/page'),
  cards: () => import('@/app/(authenticated)/cards/page'),
  goals: () => import('@/app/(authenticated)/goals/page'),
  p2p: () => import('@/app/(authenticated)/p2p/page'),
  subscriptions: () => import('@/app/(authenticated)/subscriptions/page'),
  transfer: () => import('@/app/(authenticated)/transfer/page'),
  settings: () => import('@/app/(authenticated)/settings/page'),
  security: () => import('@/app/(authenticated)/security/page'),
  business: () => import('@/app/(authenticated)/business/page'),
};