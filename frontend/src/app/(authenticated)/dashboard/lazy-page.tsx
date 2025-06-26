'use client';

import dynamic from 'next/dynamic';
import LoadingSkeleton from '@/components/performance/LoadingSkeleton';

// Lazy load the dashboard page with a custom loading component
const DashboardPage = dynamic(
  () => import('./page'),
  {
    loading: () => <LoadingSkeleton type="page" />,
    ssr: false // Disable SSR for better performance in client-only components
  }
);

export default function LazyDashboardPage() {
  return <DashboardPage />;
}