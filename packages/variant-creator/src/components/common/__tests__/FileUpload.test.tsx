import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { FileUpload } from "../FileUpload";

const validSvg = `
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <g id="provinces">
      <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
    </g>
  </svg>
`;

const invalidSvg = `
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <g id="background">
      <rect width="100" height="100" fill="blue"/>
    </g>
  </svg>
`;

beforeEach(() => {
  if (!File.prototype.text) {
    File.prototype.text = function () {
      return new Promise(resolve => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsText(this);
      });
    };
  }
});

function createFile(content: string, name: string, type: string): File {
  return new File([content], name, { type });
}

describe("FileUpload", () => {
  it("renders upload zone with instructions", () => {
    render(<FileUpload />);

    expect(
      screen.getByText("Drop SVG file here or click to upload")
    ).toBeInTheDocument();
  });

  it("shows success message for valid SVG file", async () => {
    render(<FileUpload />);

    const file = createFile(validSvg, "test.svg", "image/svg+xml");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByText("SVG valid!")).toBeInTheDocument();
    });
  });

  it("shows error message for SVG missing provinces layer", async () => {
    render(<FileUpload />);

    const file = createFile(invalidSvg, "test.svg", "image/svg+xml");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(
        screen.getByText("SVG must contain a layer named 'provinces'")
      ).toBeInTheDocument();
    });
  });

  it("shows error for non-SVG file", async () => {
    render(<FileUpload />);

    const file = createFile("plain text", "test.txt", "text/plain");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByText("Please upload an SVG file")).toBeInTheDocument();
    });
  });

  it("calls onFileValidated callback with result and content", async () => {
    const onFileValidated = vi.fn();
    render(<FileUpload onFileValidated={onFileValidated} />);

    const file = createFile(validSvg, "test.svg", "image/svg+xml");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(onFileValidated).toHaveBeenCalledWith(
        { valid: true },
        validSvg
      );
    });
  });

  it("applies dragging styles on drag over", () => {
    render(<FileUpload />);

    const dropZone = screen.getByRole("button");

    fireEvent.dragOver(dropZone);

    expect(dropZone).toHaveClass("border-primary");
  });

  it("removes dragging styles on drag leave", () => {
    render(<FileUpload />);

    const dropZone = screen.getByRole("button");

    fireEvent.dragOver(dropZone);
    expect(dropZone).toHaveClass("border-primary");

    fireEvent.dragLeave(dropZone);
    expect(dropZone).not.toHaveClass("border-primary");
  });

  it("handles file selection via click", async () => {
    render(<FileUpload />);

    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    const file = createFile(validSvg, "test.svg", "image/svg+xml");

    Object.defineProperty(input, "files", {
      value: [file],
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText("SVG valid!")).toBeInTheDocument();
    });
  });
});
