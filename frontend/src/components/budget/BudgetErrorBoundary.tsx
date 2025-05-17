import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class BudgetErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Budget component error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card variant="error" className="p-6 text-center">
          <AlertCircle className="w-12 h-12 text-[var(--primary-red)] mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-[var(--text-1)] mb-2">
            Budget Component Error
          </h3>
          <p className="text-sm text-[var(--text-2)] mb-4">
            Something went wrong while displaying budget information. Please try refreshing the page.
          </p>
          <p className="text-xs text-[var(--text-2)] mb-4 font-mono">
            {this.state.error?.message || 'Unknown error'}
          </p>
          <Button 
            variant="primary" 
            size="sm" 
            onClick={this.handleReset}
          >
            Try Again
          </Button>
        </Card>
      );
    }

    return this.props.children;
  }
}

export default BudgetErrorBoundary;