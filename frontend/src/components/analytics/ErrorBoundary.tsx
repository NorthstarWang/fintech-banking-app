'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
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

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to analytics
      text: `Error caught: ${error.message}`,
      custom_action: 'error_boundary_catch',
      data: {
        error_name: error.name,
        error_stack: error.stack,
        component_stack: errorInfo.componentStack,
        error_timestamp: new Date().toISOString(),
      },
    });

    this.setState({
      error,
      errorInfo,
    });

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by boundary:', error, errorInfo);
    }
  }

  handleReset = () => {
    
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });

    // Reload the page
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-[var(--bg-color)] flex items-center justify-center p-4">
          <Card variant="prominent" className="max-w-md w-full">
            <div className="p-8 text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--primary-red)]/10 flex items-center justify-center">
                <AlertCircle className="w-8 h-8 text-[var(--primary-red)]" />
              </div>
              
              <h2 className="text-2xl font-bold text-[var(--text-1)] mb-2">
                Oops! Something went wrong
              </h2>
              
              <p className="text-[var(--text-2)] mb-6">
                We're sorry for the inconvenience. The application encountered an unexpected error.
              </p>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="mb-6 p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] border border-[var(--border-1)] text-left">
                  <p className="text-sm font-mono text-[var(--primary-red)] break-all">
                    {this.state.error.message}
                  </p>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  variant="primary"
                  icon={<RefreshCw size={16} />}
                  onClick={this.handleReset}
                  fullWidth
                  analyticsId="error-boundary-reload"
                  analyticsLabel="Reload Page"
                >
                  Reload Page
                </Button>
                
                <Button
                  variant="secondary"
                  onClick={() => {
                    window.location.href = '/dashboard';
                  }}
                  fullWidth
                  analyticsId="error-boundary-home"
                  analyticsLabel="Go to Dashboard"
                >
                  Go to Dashboard
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
