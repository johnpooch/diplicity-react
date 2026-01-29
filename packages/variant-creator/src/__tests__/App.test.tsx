import { render, screen } from "@testing-library/react";
import App from "../App";

describe("App", () => {
  it("renders the Variant Creator heading", () => {
    render(<App />);
    expect(screen.getByText("Variant Creator")).toBeInTheDocument();
  });

  it("renders the Get Started button", () => {
    render(<App />);
    expect(
      screen.getByRole("button", { name: /get started/i })
    ).toBeInTheDocument();
  });
});
