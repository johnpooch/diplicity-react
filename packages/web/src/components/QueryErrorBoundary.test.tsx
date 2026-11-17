import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AxiosError, AxiosHeaders } from "axios";
import * as Sentry from "@sentry/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryErrorBoundary } from "./QueryErrorBoundary";

vi.mock("@sentry/react", () => ({ captureException: vi.fn() }));

const responseError = (status: number) =>
  new AxiosError("Request failed", "ERR_BAD_REQUEST", undefined, undefined, {
    status,
    statusText: "",
    data: {},
    headers: {},
    config: { headers: new AxiosHeaders() },
  });

const Thrower: React.FC<{ error: Error }> = ({ error }) => {
  throw error;
};

const renderBoundary = (error: Error) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <QueryErrorBoundary>
        <Thrower error={error} />
      </QueryErrorBoundary>
    </QueryClientProvider>
  );

describe("QueryErrorBoundary", () => {
  beforeEach(() => {
    vi.mocked(Sentry.captureException).mockReset();
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("reports unexpected errors to Sentry", () => {
    renderBoundary(responseError(500));

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(Sentry.captureException).toHaveBeenCalled();
  });

  it("does not report permission refusals to Sentry", () => {
    renderBoundary(responseError(403));

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(Sentry.captureException).not.toHaveBeenCalled();
  });
});
