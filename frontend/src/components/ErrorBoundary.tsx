'use client';

import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import Button from './ui/Button';
import Card from './ui/Card';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to analytics
      error_name: error.name,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

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
          <Card variant="error" className="max-w-lg w-full p-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[rgba(var(--primary-red),0.1)] mb-4">
                <AlertTriangle className="w-8 h-8 text-[var(--primary-red)]" />
              </div>
              
              <h2 className="text-2xl font-bold text-[var(--text-1)] mb-2">
                Oops! Something went wrong
              </h2>
              
              <p className="text-[var(--text-2)] mb-6">
                We encountered an unexpected error. Don't worry, your data is safe.
              </p>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="text-left mb-6 p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] border border-[var(--border-1)]">
                  <summary className="cursor-pointer font-medium text-[var(--text-1)] mb-2">
                    Error Details (Development Only)
                  </summary>
                  <pre className="text-xs text-[var(--text-2)] overflow-auto">
                    {this.state.error.message}
                    {this.state.errorInfo?.componentStack}
                  </pre>
                </details>
              )}

              <div className="flex gap-3 justify-center">
                <Button
                  variant="secondary"
                  onClick={() => window.history.back()}
                >
                  Go Back
                </Button>
                <Button
                  variant="primary"
                  icon={<RefreshCw size={18} />}
                  onClick={this.handleReset}
                >
                  Reload Page
                </Button>
              </div>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
