import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BlogList } from "./index";
import { blogPosts } from "@/mocks/fixtures";

const mockUseBlogListSuspense = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal();
  return {
    ...(actual as Record<string, unknown>),
    useBlogListSuspense: () => mockUseBlogListSuspense(),
  };
});

const renderBlogList = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <BlogList />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

beforeEach(() => {
  mockUseBlogListSuspense.mockReset();
  mockUseBlogListSuspense.mockReturnValue({ data: blogPosts });
});

describe("BlogList", () => {
  it("lists every post with its summary", async () => {
    renderBlogList();

    expect(await screen.findByText("Spring 1901 update")).toBeInTheDocument();
    expect(
      screen.getByText("Welcome to the Diplicity blog")
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Development news, strategy notes and community announcements."
      )
    ).toBeInTheDocument();
  });

  it("links each post to its own page", async () => {
    renderBlogList();

    const link = await screen.findByRole("link", {
      name: /Spring 1901 update/,
    });
    expect(link).toHaveAttribute("href", "/blog/spring-1901-update");
  });

  it("shows the empty state when there are no posts", async () => {
    mockUseBlogListSuspense.mockReturnValue({ data: [] });
    renderBlogList();

    expect(await screen.findByText("No posts yet")).toBeInTheDocument();
  });
});
