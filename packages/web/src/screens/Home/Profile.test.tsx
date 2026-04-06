import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Profile } from "./Profile";
import { themeStorage } from "@/theme/themeStorage";

const mockUserProfile = {
  id: 1,
  email: "player@example.com",
  name: "Test Player",
  picture: null,
};

const mockSetPreference = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useUserRetrieveSuspense: () => ({ data: mockUserProfile }),
  useUserUpdatePartialUpdate: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
  getUserRetrieveQueryKey: () => ["user"],
}));

vi.mock("@/hooks/useMessaging", () => ({
  useMessaging: () => ({
    enableMessaging: vi.fn(),
    disableMessaging: vi.fn(),
    enabled: false,
    permissionDenied: false,
    error: null,
  }),
}));

vi.mock("@/auth", () => ({
  useAuth: () => ({ logout: vi.fn() }),
}));

vi.mock("@/theme/useTheme", () => ({
  useTheme: () => ({
    preference: "system",
    resolvedTheme: "light",
    setPreference: mockSetPreference,
  }),
}));

// Default matchMedia mock (jsdom doesn't implement it)
const createMatchMediaMock = (prefersDark = false) =>
  vi.fn().mockImplementation(
    (query: string) =>
      ({
        matches: query === "(prefers-color-scheme: dark)" ? prefersDark : false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }) as unknown as MediaQueryList
  );

const renderProfile = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Profile />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("Profile - Appearance section", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.classList.remove("dark");
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: createMatchMediaMock(false),
    });
    themeStorage.initialize();
  });

  it("renders the Appearance section heading", async () => {
    renderProfile();
    expect(await screen.findByText("Appearance")).toBeInTheDocument();
  });

  it("renders the theme selector with System as default", async () => {
    renderProfile();
    expect(await screen.findByText("System")).toBeInTheDocument();
  });

  it("renders the Theme label", async () => {
    renderProfile();
    expect(await screen.findByText("Theme")).toBeInTheDocument();
  });

  it("renders the theme select trigger", async () => {
    renderProfile();
    expect(await screen.findByRole("combobox")).toBeInTheDocument();
  });

  it("Appearance section appears before Notifications section", async () => {
    renderProfile();
    const headings = await screen.findAllByRole("heading", { level: 2 });
    const headingTexts = headings.map(h => h.textContent);
    const appearanceIndex = headingTexts.indexOf("Appearance");
    const notificationsIndex = headingTexts.indexOf("Notifications");
    expect(appearanceIndex).toBeGreaterThanOrEqual(0);
    expect(notificationsIndex).toBeGreaterThanOrEqual(0);
    expect(appearanceIndex).toBeLessThan(notificationsIndex);
  });
});
