import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { JsonUpload } from "../JsonUpload";
import type { VariantDefinition } from "@/types/variant";

const createValidVariant = (): VariantDefinition => ({
  name: "Test Variant",
  description: "A test variant",
  author: "Test Author",
  version: "1.0.0",
  soloVictorySCCount: 18,
  nations: [{ id: "england", name: "England", color: "#FF0000" }],
  provinces: [
    {
      id: "lon",
      elementId: "path1",
      name: "London",
      type: "coastal",
      path: "M0,0 L10,0 L10,10 Z",
      homeNation: "england",
      supplyCenter: true,
      startingUnit: { type: "Fleet" },
      adjacencies: ["eng"],
      labels: [{ text: "London", position: { x: 5, y: 5 }, source: "svg" }],
      unitPosition: { x: 5, y: 5 },
      dislodgedUnitPosition: { x: 20, y: 20 },
      supplyCenterPosition: { x: -7, y: -7 },
    },
  ],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 100, height: 100 },
  textElements: [],
});

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

describe("JsonUpload", () => {
  it("renders upload zone with instructions", () => {
    render(<JsonUpload />);

    expect(
      screen.getByText("Drop JSON file here or click to upload")
    ).toBeInTheDocument();
  });

  it("shows success message for valid JSON file", async () => {
    const variant = createValidVariant();
    const json = JSON.stringify(variant);

    render(<JsonUpload />);

    const file = createFile(json, "variant.json", "application/json");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByText("JSON valid!")).toBeInTheDocument();
    });
  });

  it("shows error message for invalid JSON syntax", async () => {
    render(<JsonUpload />);

    const file = createFile("{ invalid json }", "test.json", "application/json");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByText("Invalid JSON format")).toBeInTheDocument();
    });
  });

  it("shows error message for invalid variant structure", async () => {
    const invalidVariant = { name: "Test", provinces: "not an array" };
    const json = JSON.stringify(invalidVariant);

    render(<JsonUpload />);

    const file = createFile(json, "test.json", "application/json");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByText("Invalid variant structure")).toBeInTheDocument();
    });
  });

  it("shows error for non-JSON file", async () => {
    render(<JsonUpload />);

    const file = createFile("plain text", "test.txt", "text/plain");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByText("Please upload a JSON file")).toBeInTheDocument();
    });
  });

  it("shows error for empty provinces array", async () => {
    const variant = createValidVariant();
    variant.provinces = [];
    const json = JSON.stringify(variant);

    render(<JsonUpload />);

    const file = createFile(json, "test.json", "application/json");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(
        screen.getByText("Variant must contain at least one province")
      ).toBeInTheDocument();
    });
  });

  it("calls onFileValidated callback with result and variant on success", async () => {
    const variant = createValidVariant();
    const json = JSON.stringify(variant);
    const onFileValidated = vi.fn();

    render(<JsonUpload onFileValidated={onFileValidated} />);

    const file = createFile(json, "variant.json", "application/json");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(onFileValidated).toHaveBeenCalledWith(
        expect.objectContaining({ valid: true }),
        expect.objectContaining({ name: "Test Variant" })
      );
    });
  });

  it("calls onFileValidated callback with null variant on failure", async () => {
    const onFileValidated = vi.fn();

    render(<JsonUpload onFileValidated={onFileValidated} />);

    const file = createFile("{ bad }", "test.json", "application/json");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(onFileValidated).toHaveBeenCalledWith(
        expect.objectContaining({ valid: false }),
        null
      );
    });
  });

  it("applies dragging styles on drag over", () => {
    render(<JsonUpload />);

    const dropZone = screen.getByRole("button");

    fireEvent.dragOver(dropZone);

    expect(dropZone).toHaveClass("border-primary");
  });

  it("removes dragging styles on drag leave", () => {
    render(<JsonUpload />);

    const dropZone = screen.getByRole("button");

    fireEvent.dragOver(dropZone);
    expect(dropZone).toHaveClass("border-primary");

    fireEvent.dragLeave(dropZone);
    expect(dropZone).not.toHaveClass("border-primary");
  });

  it("handles file selection via click", async () => {
    const variant = createValidVariant();
    const json = JSON.stringify(variant);

    render(<JsonUpload />);

    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    const file = createFile(json, "variant.json", "application/json");

    Object.defineProperty(input, "files", {
      value: [file],
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText("JSON valid!")).toBeInTheDocument();
    });
  });

  it("displays validation details when available", async () => {
    const invalidVariant = { name: "Test", provinces: [{}] };
    const json = JSON.stringify(invalidVariant);

    render(<JsonUpload />);

    const file = createFile(json, "test.json", "application/json");
    const dropZone = screen.getByRole("button");

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByText(/Error at/)).toBeInTheDocument();
    });
  });
});
