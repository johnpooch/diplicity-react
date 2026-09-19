import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ProfilePictureEditor } from "./ProfilePictureEditor";

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

const {
  mockUploadPicture,
  mockRemovePicture,
  mockToastError,
  mockDownscaleImage,
} = vi.hoisted(() => ({
  mockUploadPicture: vi.fn(),
  mockRemovePicture: vi.fn(),
  mockToastError: vi.fn(),
  mockDownscaleImage: vi.fn(),
}));

vi.mock("@/api/generated/endpoints", () => ({
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

const renderEditor = (picture: string | null = null) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfilePictureEditor userId={1} name="Test Player" picture={picture} />
    </QueryClientProvider>
  );
};

const getFileInput = (container: HTMLElement) =>
  container.querySelector<HTMLInputElement>('input[type="file"]')!;

describe("ProfilePictureEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockDownscaleImage.mockImplementation(async (file: File) => file);
  });

  it("uploads the chosen file", async () => {
    const user = userEvent.setup();
    const { container } = renderEditor();
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
    const { container } = renderEditor();

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
    const { container } = renderEditor();

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
    renderEditor(null);

    await user.click(screen.getByRole("button", { name: "Change picture" }));

    expect(
      await screen.findByRole("menuitem", { name: "Upload picture" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("menuitem", { name: "Remove picture" })
    ).not.toBeInTheDocument();
  });

  it("removes the picture when one is set", async () => {
    const user = userEvent.setup();
    renderEditor("https://example.com/me.png");

    await user.click(screen.getByRole("button", { name: "Change picture" }));
    await user.click(
      await screen.findByRole("menuitem", { name: "Remove picture" })
    );

    expect(mockRemovePicture).toHaveBeenCalled();
  });
});
