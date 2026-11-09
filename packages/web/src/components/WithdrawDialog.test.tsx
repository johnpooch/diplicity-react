import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WithdrawDialog } from "./WithdrawDialog";

const onConfirm = vi.fn();

const renderDialog = (isFirstYear = false) =>
  render(
    <WithdrawDialog
      open
      onOpenChange={vi.fn()}
      isFirstYear={isFirstYear}
      onConfirm={onConfirm}
    />
  );

describe("WithdrawDialog", () => {
  beforeEach(() => {
    onConfirm.mockReset();
    Element.prototype.hasPointerCapture = () => false;
    Element.prototype.scrollIntoView = () => {};
  });

  it("warns about commitment in the first year", () => {
    renderDialog(true);

    expect(
      screen.getByText(
        "Withdrawing in the first year impacts your commitment score negatively. Your seat will be offered to a replacement. You cannot rejoin this game."
      )
    ).toBeInTheDocument();
  });

  it("reassures about commitment after the first year", () => {
    renderDialog(false);

    expect(
      screen.getByText(
        "Your commitment rating is not affected. You cannot rejoin this game."
      )
    ).toBeInTheDocument();
  });

  it("requires a reason before withdrawing", () => {
    renderDialog();

    expect(screen.getByRole("button", { name: "Withdraw" })).toBeDisabled();
  });

  it("withdraws with the chosen reason", async () => {
    renderDialog();

    await userEvent.click(
      screen.getByRole("combobox", { name: "Why are you withdrawing?" })
    );
    await userEvent.click(
      screen.getByRole("option", { name: "I don't like my nation" })
    );
    await userEvent.click(screen.getByRole("button", { name: "Withdraw" }));

    expect(onConfirm).toHaveBeenCalledWith("dislike_nation");
  });
});
