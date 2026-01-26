import React from "react";
import * as Sentry from "@sentry/react";
import { DiplicityLogo } from "./DiplicityLogo";
import { Button } from "@/components/ui/button";

interface ErrorFallbackUIProps {
  error: Error;
}

export const ErrorFallbackUI: React.FC<ErrorFallbackUIProps> = ({ error }) => {
  return (
    <div className="max-w-sm mx-auto">
      <div className="flex flex-col items-center justify-center min-h-screen text-center gap-6">
        <DiplicityLogo />
        <h1 className="text-2xl font-bold">Something went wrong</h1>
        <p className="text-muted-foreground">
          We've been notified of the issue and are working to fix it.
          Please try refreshing the page or returning to the home screen.
        </p>
        {import.meta.env.MODE === "development" && (
          <div className="mt-2 p-4 bg-destructive/20 rounded text-left w-full">
            <pre className="text-xs whitespace-pre-wrap">{error.toString()}</pre>
          </div>
        )}
        <Button variant="outline" onClick={() => window.location.href = "/"}>
          Go Home
        </Button>
      </div>
    </div>
  );
};

interface ErrorFallbackProps {
  error: unknown;
  componentStack: string;
  eventId: string;
  resetError: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error }) => {
  const errorObject = error instanceof Error ? error : new Error(String(error));
  return <ErrorFallbackUI error={errorObject} />;
};

export const ErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Sentry.ErrorBoundary
      fallback={(props) => <ErrorFallback {...props} />}
      showDialog={false}
    >
      {children}
    </Sentry.ErrorBoundary>
  );
};
