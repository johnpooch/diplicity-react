import React, { Component, ReactNode } from "react";
import { useQueryErrorResetBoundary } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/Notice";
import { AlertCircle } from "lucide-react";

interface QueryErrorFallbackProps {
  error: Error;
  onReset: () => void;
}

const QueryErrorFallback: React.FC<QueryErrorFallbackProps> = ({
  error,
  onReset,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <Notice
        icon={AlertCircle}
        title="Something went wrong"
        message="We couldn't load this content. Please try again."
        actions={<Button onClick={onReset}>Try Again</Button>}
      />
      {import.meta.env.MODE === "development" && (
        <div className="mt-4 p-4 bg-destructive/10 rounded-md text-left w-full max-w-md">
          <pre className="text-xs whitespace-pre-wrap text-destructive">
            {error.toString()}
          </pre>
        </div>
      )}
    </div>
  );
};

interface ErrorBoundaryClassProps {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
  renderFallback?: (error: Error, onReset: () => void) => ReactNode;
}

interface ErrorBoundaryClassState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundaryClass extends Component<
  ErrorBoundaryClassProps,
  ErrorBoundaryClassState
> {
  constructor(props: ErrorBoundaryClassProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryClassState {
    return { hasError: true, error };
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.renderFallback) {
        return this.props.renderFallback(this.state.error, this.handleReset);
      }

      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <QueryErrorFallback
          error={this.state.error}
          onReset={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

interface QueryErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  renderFallback?: (error: Error, onReset: () => void) => ReactNode;
}

const QueryErrorBoundary: React.FC<QueryErrorBoundaryProps> = ({
  children,
  fallback,
  renderFallback,
}) => {
  const { reset } = useQueryErrorResetBoundary();

  return (
    <ErrorBoundaryClass
      onReset={reset}
      fallback={fallback}
      renderFallback={renderFallback}
    >
      {children}
    </ErrorBoundaryClass>
  );
};

export { QueryErrorBoundary, QueryErrorFallback, ErrorBoundaryClass };
