import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { HomeLayout } from "./HomeLayout";

const userProfile = vi.fn();
const isMobile = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useUserRetrieveSuspense: () => ({ data: userProfile() }),
}));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => isMobile() }));

vi.mock("@/components/SidebarUserArea", () => ({ SidebarUserArea: () => null }));

vi.mock("@/components/OfflineBanner", () => ({ OfflineBanner: () => null }));

const renderLayout = (path = "/") =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <HomeLayout>
          <p>Content</p>
        </HomeLayout>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("HomeLayout moderation entry", () => {
  beforeEach(() => {
    isMobile.mockReturnValue(false);
    userProfile.mockReturnValue({ name: "Mia", isModerator: true });
  });

  it("links moderators to the queue on desktop", () => {
    renderLayout();

    expect(screen.getByRole("link", { name: "Moderation" })).toHaveAttribute(
      "href",
      "/moderation"
    );
  });

  it("marks the entry active on moderation pages", () => {
    renderLayout("/moderation/reports/3");

    expect(screen.getByRole("link", { name: "Moderation" })).toHaveAttribute(
      "data-active",
      "true"
    );
  });

  it("is hidden from players who are not moderators", () => {
    userProfile.mockReturnValue({ name: "Pat", isModerator: false });
    renderLayout();

    expect(screen.queryByRole("link", { name: "Moderation" })).not.toBeInTheDocument();
    expect(screen.queryByText("Moderation")).not.toBeInTheDocument();
  });

  it("adds nothing to mobile navigation", () => {
    isMobile.mockReturnValue(true);
    renderLayout();

    expect(screen.queryByText("Moderation")).not.toBeInTheDocument();
  });
});
