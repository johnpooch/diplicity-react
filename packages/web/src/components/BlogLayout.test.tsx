import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, it, expect } from "vitest";
import { BlogLayout } from "./BlogLayout";

const renderBlogLayout = () =>
  render(
    <MemoryRouter>
      <BlogLayout>
        <p>Post content</p>
      </BlogLayout>
    </MemoryRouter>
  );

describe("BlogLayout", () => {
  it("links the blog title back to the blog index", () => {
    renderBlogLayout();

    expect(
      screen.getByRole("link", { name: /Diplicity Blog/ })
    ).toHaveAttribute("href", "/blog");
  });

  it("links to the app", () => {
    renderBlogLayout();

    expect(screen.getByRole("link", { name: "App" })).toHaveAttribute(
      "href",
      "/"
    );
  });

  it("renders its content", () => {
    renderBlogLayout();

    expect(screen.getByText("Post content")).toBeInTheDocument();
  });
});
