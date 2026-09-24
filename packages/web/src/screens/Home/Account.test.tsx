import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Account } from "./Account";
import { themeStorage } from "@/theme/themeStorage";

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

const mockUserProfile: {
  id: number;
  userId: number;
  email: string;
  name: string;
  picture: string | null;
} = {
  id: 1,
  userId: 1,
  email: "player@example.com",
  name: "Test Player",
  picture: null,
};

let mockPublicProfile: {
  id: number;
  name: string;
  picture: string | null;
  createdAt: string;
  totalGames: number;
  soloWins: number;
  draws: number;
  losses: number;
  nmrRate: number;
  cdRate: number;
  reliabilityTier: string;
  commitment: string;
} = {
  id: 1,
  name: "Test Player",
  picture: null,
  createdAt: "2025-01-15T12:00:00Z",
  totalGames: 12,
  soloWins: 1,
  draws: 3,
  losses: 6,
  nmrRate: 0.05,
  cdRate: 0,
  reliabilityTier: "reliable",
  commitment: "high",
};

const mockSetPreference = vi.fn();
const {
  mockUploadPicture,
  mockRemovePicture,
  mockToastError,
  mockDownscaleImage,
  mockUpdateName,
} = vi.hoisted(() => ({
  mockUploadPicture: vi.fn(),
  mockRemovePicture: vi.fn(),
  mockToastError: vi.fn(),
  mockDownscaleImage: vi.fn(),
  mockUpdateName: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("@/api/generated/endpoints", () => ({
  useUserRetrieveSuspense: () => ({ data: mockUserProfile }),
  useUsersRetrieveSuspense: () => ({ data: mockPublicProfile }),
  useUserUpdatePartialUpdate: () => ({
    mutateAsync: mockUpdateName,
    isPending: false,
  }),
  useUserPictureUpdate: () => ({
    mutateAsync: mockUploadPicture,
    isPending: false,
  }),
  useUserPictureDestroy: () => ({
    mutateAsync: mockRemovePicture,
    isPending: false,
  }),
  getUserRetrieveQueryKey: () => ["user"],
  getUsersRetrieveQueryKey: (userId: number) => ["users", userId],
}));

vi.mock("sonner", () => ({
  toast: { error: mockToastError },
}));

vi.mock("@/utils/downscaleImage", () => ({
  downscaleImage: mockDownscaleImage,
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

const renderAccount = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Account />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("Account - Appearance section", () => {
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
    renderAccount();
    expect(await screen.findByText("Appearance")).toBeInTheDocument();
  });

  it("renders the theme selector with System as default", async () => {
    renderAccount();
    expect(await screen.findByText("System")).toBeInTheDocument();
  });

  it("renders the theme radio options", async () => {
    renderAccount();
    expect(await screen.findByRole("radio", { name: "System" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Light" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Dark" })).toBeInTheDocument();
  });

  it("Appearance section appears before Notifications section", async () => {
    renderAccount();
    const headings = await screen.findAllByRole("heading", { level: 2 });
    const headingTexts = headings.map(h => h.textContent);
    const appearanceIndex = headingTexts.indexOf("Appearance");
    const notificationsIndex = headingTexts.indexOf("Notifications");
    expect(appearanceIndex).toBeGreaterThanOrEqual(0);
    expect(notificationsIndex).toBeGreaterThanOrEqual(0);
    expect(appearanceIndex).toBeLessThan(notificationsIndex);
  });
});

describe("Account - profile picture", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockDownscaleImage.mockImplementation(async (file: File) => file);
    mockPublicProfile = { ...mockPublicProfile, picture: null };
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: createMatchMediaMock(false),
    });
    themeStorage.initialize();
  });

  const getFileInput = (container: HTMLElement) =>
    container.querySelector<HTMLInputElement>('input[type="file"]')!;

  it("uploads the chosen file", async () => {
    const user = userEvent.setup();
    const { container } = renderAccount();
    const file = new File(["image"], "me.png", { type: "image/png" });

    await user.upload(getFileInput(container), file);

    expect(mockUploadPicture).toHaveBeenCalledWith({ data: { picture: file } });
    expect(mockToastError).not.toHaveBeenCalled();
  });

  it("uploads the downscaled file rather than the original", async () => {
    const original = new File(["original"], "me.png", { type: "image/png" });
    const downscaled = new File(["small"], "me.png", { type: "image/png" });
    mockDownscaleImage.mockResolvedValue(downscaled);
    const user = userEvent.setup();
    const { container } = renderAccount();

    await user.upload(getFileInput(container), original);

    expect(mockDownscaleImage).toHaveBeenCalledWith(original);
    expect(mockUploadPicture).toHaveBeenCalledWith({
      data: { picture: downscaled },
    });
  });

  it("surfaces the server's message when an upload is rejected", async () => {
    mockUploadPicture.mockRejectedValue({
      response: {
        data: { picture: ["Picture is too large (max 2097152 bytes)."] },
      },
    });
    const user = userEvent.setup();
    const { container } = renderAccount();

    await user.upload(
      getFileInput(container),
      new File(["image"], "me.png", { type: "image/png" })
    );

    await waitFor(() =>
      expect(mockToastError).toHaveBeenCalledWith(
        "Picture is too large (max 2097152 bytes)."
      )
    );
  });

  it("offers no remove option when no picture is set", async () => {
    const user = userEvent.setup();
    renderAccount();

    await user.click(screen.getByRole("button", { name: "Change picture" }));

    expect(
      await screen.findByRole("menuitem", { name: "Upload picture" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("menuitem", { name: "Remove picture" })
    ).not.toBeInTheDocument();
  });

  it("removes the picture when one is set", async () => {
    mockPublicProfile = {
      ...mockPublicProfile,
      picture: "https://example.com/me.png",
    };
    const user = userEvent.setup();
    renderAccount();

    await user.click(screen.getByRole("button", { name: "Change picture" }));
    await user.click(
      await screen.findByRole("menuitem", { name: "Remove picture" })
    );

    expect(mockRemovePicture).toHaveBeenCalled();
  });
});

describe("Account - name and log out", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPublicProfile = { ...mockPublicProfile, name: "Test Player" };
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: createMatchMediaMock(false),
    });
    themeStorage.initialize();
  });

  it("renders the player's name and a log out button", async () => {
    renderAccount();
    expect(await screen.findByText("Test Player")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Log out" })
    ).toBeInTheDocument();
  });

  it("saves an edited name", async () => {
    const user = userEvent.setup();
    renderAccount();

    await user.click(await screen.findByRole("button", { name: "Edit name" }));
    await user.clear(screen.getByDisplayValue("Test Player"));
    await user.type(screen.getByRole("textbox"), "New Name");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(mockUpdateName).toHaveBeenCalledWith({ data: { name: "New Name" } });
  });
});
