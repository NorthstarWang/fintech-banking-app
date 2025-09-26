'use client';

import { useEffect } from "react";
import { LoginForm } from '@/components/LoginForm';

export default function Home() {
  useEffect(() => {
    // Initialize session on component mount
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[var(--primary-blue)] to-[var(--primary-indigo)]">
      <div className="w-full max-w-md">
        <LoginForm />
      </div>
    </div>
  );
}