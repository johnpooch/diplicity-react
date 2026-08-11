import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AxiosError, AxiosHeaders } from "axios";
import type { AxiosResponse } from "axios";
import { ErrorBoundaryClass } from "./QueryErrorBoundary";

const captureException = vi.fn();

vi.mock("@sentry/react", () => ({
  captureException: (error: unknown) => captureException(error),
}));

const responseError = (status: number) => {
  const config = { headers: new AxiosHeaders() };
  const response = {
    status,
    statusText: "",
    data: null,
    headers: {},
    config,
  } as AxiosResponse;
  return new AxiosError(
    `Request failed with status code ${status}`,
    AxiosError.ERR_BAD_REQUEST,
    config,
    undefined,
    response
  );
};

const Thrower: React.FC<{ error: Error }> = ({ error }) => {
  throw error;
};

const renderWithError = (error: Error) =>
  render(
    <ErrorBoundaryClass>
      <Thrower error={error} />
    </ErrorBoundaryClass>
  );

describe("QueryErrorBoundary", () => {
  beforeEach(() => {
    captureException.mockReset();
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("renders the not found notice for a 404 without reporting it", () => {
    renderWithError(responseError(404));

    expect(
      screen.getByText("This game is no longer available")
    ).toBeInTheDocument();
    expect(captureException).not.toHaveBeenCalled();
  });

  it("renders the generic fallback for a 500 and reports it", () => {
    const error = responseError(500);
    renderWithError(error);

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(captureException).toHaveBeenCalledWith(error);
  });

  it("renders the offline notice for a network error without reporting it", () => {
    renderWithError(new AxiosError("Network Error", AxiosError.ERR_NETWORK));

    expect(screen.getByText("No internet connection")).toBeInTheDocument();
    expect(captureException).not.toHaveBeenCalled();
  });
});
