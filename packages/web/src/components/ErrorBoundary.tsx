import React from "react";
import * as Sentry from "@sentry/react";
import { Box, Container, Typography, Button } from "@mui/material";
import { DiplicityLogo } from "./DiplicityLogo";

interface ErrorFallbackUIProps {
  error: Error;
}

export const ErrorFallbackUI: React.FC<ErrorFallbackUIProps> = ({ error }) => {
  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          textAlign: "center",
          gap: 3,
        }}
      >
        <DiplicityLogo />
        <Typography variant="h1">Something went wrong</Typography>
        <Typography variant="body1" color="text.secondary">
          We've been notified of the issue and are working to fix it.
          Please try refreshing the page or returning to the home screen.
        </Typography>
        {import.meta.env.MODE === "development" && (
          <Box
            sx={{
              mt: 2,
              p: 2,
              bgcolor: "error.light",
              borderRadius: 1,
              textAlign: "left",
              width: "100%",
            }}
          >
            <Typography variant="caption" component="pre" sx={{ whiteSpace: "pre-wrap" }}>
              {error.toString()}
            </Typography>
          </Box>
        )}
        <Button variant="outlined" onClick={() => window.location.href = "/"}>
          Go Home
        </Button>
      </Box>
    </Container>
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
