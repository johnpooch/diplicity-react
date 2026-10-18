import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AxiosError, AxiosHeaders } from "axios";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BlogPost } from "./index";
import { blogPosts } from "@/mocks/fixtures";

const mockUseBlogRetrieveSuspense = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal();
  return {
    ...(actual as Record<string, unknown>),
    useBlogRetrieveSuspense: (slug: string) =>
      mockUseBlogRetrieveSuspense(slug),
  };
});

const renderBlogPost = (slug = "spring-1901-update") => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/blog/${slug}`]}>
        <Routes>
          <Route path="/blog/:slug" element={<BlogPost />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

beforeEach(() => {
  mockUseBlogRetrieveSuspense.mockReset();
  mockUseBlogRetrieveSuspense.mockImplementation((slug: string) => ({
    data: blogPosts.find(post => post.slug === slug),
  }));
});

describe("BlogPost", () => {
  it("fetches the post named in the URL", async () => {
    renderBlogPost("welcome");

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "Welcome to the Diplicity blog",
      })
    ).toBeInTheDocument();
    expect(mockUseBlogRetrieveSuspense).toHaveBeenCalledWith("welcome");
  });

  it("renders the Markdown body", async () => {
    renderBlogPost();

    expect(
      await screen.findByRole("heading", { level: 2, name: "Game masters" })
    ).toBeInTheDocument();
    expect(screen.getByText("game master").tagName).toBe("STRONG");
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Discord" })).toHaveAttribute(
      "href",
      "https://discord.gg/cwjzxEqTuN"
    );
  });

  it("does not render raw HTML or images in the body", async () => {
    mockUseBlogRetrieveSuspense.mockReturnValue({
      data: {
        ...blogPosts[1],
        body: '<script>alert("x")</script>\n\n![Map](https://example.com/map.png)',
      },
    });
    const { container } = renderBlogPost("welcome");

    await screen.findByRole("heading", { level: 1 });
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
  });

  it("shows a not found notice for an unknown slug", async () => {
    mockUseBlogRetrieveSuspense.mockImplementation(() => {
      throw new AxiosError(
        "Not Found",
        "ERR_BAD_REQUEST",
        undefined,
        undefined,
        {
          status: 404,
          statusText: "Not Found",
          data: {},
          headers: {},
          config: { headers: new AxiosHeaders() },
        }
      );
    });
    vi.spyOn(console, "error").mockImplementation(() => {});
    renderBlogPost("missing");

    expect(await screen.findByText("Post not found")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "See all posts" })).toHaveAttribute(
      "href",
      "/blog"
    );
  });
});
