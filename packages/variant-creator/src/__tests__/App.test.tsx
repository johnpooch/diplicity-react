import { render, screen } from "@testing-library/react";
import App from "../App";

describe("App", () => {
  it("renders the Diplicity Variant Creator heading", () => {
    render(<App />);
    expect(screen.getByText("Diplicity Variant Creator")).toBeInTheDocument();
  });

  it("renders the file upload zone", () => {
    render(<App />);
    expect(
      screen.getByText("Drop SVG file here or click to upload")
    ).toBeInTheDocument();
  });
});
