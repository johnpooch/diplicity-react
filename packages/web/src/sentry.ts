import * as Sentry from "@sentry/react";

export function initializeSentry() {
  const sentryDsn = import.meta.env.VITE_SENTRY_DSN;

  if (!sentryDsn) {
    console.log(
      "[Sentry] VITE_SENTRY_DSN not set, skipping Sentry initialization"
    );
    return;
  }

  const environment = detectEnvironment();

  Sentry.init({
    dsn: sentryDsn,
    environment,
    sampleRate: 1.0,
    tracesSampleRate: environment === "development" ? 1.0 : 0.5,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    sendDefaultPii: false,

    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],

    beforeSend(event) {
      if (event.request?.headers) {
        delete event.request.headers.Authorization;
      }
      return event;
    },
  });

  console.log(
    `[Sentry] Initialized successfully in '${environment}' environment`
  );
}

function detectEnvironment(): string {
  const mode = import.meta.env.MODE;

  if (mode === "development") {
    return "development";
  } else if (mode === "production") {
    return "production";
  } else {
    return mode || "unknown";
  }
}
