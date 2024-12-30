import type { Meta, StoryObj } from "@storybook/react";
import { fn, userEvent, within, expect } from "@storybook/test";
import { CreateOrder } from "./CreateOrder";
import { GameProviderContext } from "../GameProvider";
import { createCreateOrderReducer } from "../GameProvider/GameProvider.util";
import { fixtures } from "../../common/fixtures";

const createOrderReducer = createCreateOrderReducer(
  fixtures.variants.variant,
  fixtures.game.startedGame,
  fixtures.listPhases.startedGame[5],
  fixtures.listOptions.startedGame
);

const meta: Meta<{
  onSubmit: (selectedOptions: string[]) => Promise<void>;
  onClose: () => void;
}> = {
  title: "Components/CreateOrder",
  component: CreateOrder,
  parameters: {
    layout: "fullscreen",
    viewport: {
      defaultViewport: "mobile1",
    },
  },
  args: {
    onSubmit: fn(),
    onClose: fn(),
  },
  render: (args) => (
    <GameProviderContext.Provider
      value={{
        onSubmitCreateOrder: args.onSubmit,
        onCloseCreateOrder: args.onClose,
        createOrderReducer: createOrderReducer,
      }}
    >
      <CreateOrder />
    </GameProviderContext.Provider>
  ),
};

export default meta;

type Story = StoryObj<typeof meta>;

export const SelectUnit: Story = {};

export const SelectOrderType: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const bulgariaButton = canvas.getByRole("button", { name: "Bulgaria" });
    await userEvent.click(bulgariaButton);
  },
};

export const SelectTarget: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const bulgariaButton = canvas.getByRole("button", { name: "Bulgaria" });
    await userEvent.click(bulgariaButton);
    const moveButton = canvas.getByRole("button", { name: "Move" });
    await userEvent.click(moveButton);
  },
};

export const SelectAux: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const bulgariaButton = canvas.getByRole("button", { name: "Bulgaria" });
    await userEvent.click(bulgariaButton);
    const supportButton = canvas.getByRole("button", { name: "Support" });
    await userEvent.click(supportButton);
    const constantinopleButton = canvas.getByRole("button", {
      name: "Constantinople",
    });
    userEvent.click(constantinopleButton);
  },
};

export const ConfirmHold: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const bulgariaButton = canvas.getByRole("button", { name: "Bulgaria" });
    await userEvent.click(bulgariaButton);
    const holdButton = canvas.getByRole("button", { name: "Hold" });
    await userEvent.click(holdButton);
  },
};

export const ConfirmMove: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const bulgariaButton = canvas.getByRole("button", { name: "Bulgaria" });
    await userEvent.click(bulgariaButton);
    const moveButton = canvas.getByRole("button", { name: "Move" });
    await userEvent.click(moveButton);
    const constantinopleButton = canvas.getByRole("button", {
      name: "Constantinople",
    });
    await userEvent.click(constantinopleButton);
  },
};

export const ConfirmSupport: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const bulgariaButton = canvas.getByRole("button", { name: "Bulgaria" });
    await userEvent.click(bulgariaButton);
    const supportButton = canvas.getByRole("button", { name: "Support" });
    await userEvent.click(supportButton);
    const constantinopleButton = canvas.getByRole("button", {
      name: "Constantinople",
    });
    await userEvent.click(constantinopleButton);
    const bulgariaButton2 = canvas.getByRole("button", { name: "Bulgaria" });
    await userEvent.click(bulgariaButton2);
  },
};

export const ClickClose: Story = {
  play: async ({ args, canvasElement }) => {
    const canvas = within(canvasElement);
    const button = canvas.getByRole("button", { name: "Close" });
    await userEvent.click(button);
    expect(args.onClose).toHaveBeenCalled();
  },
};

export const ClickSubmit: Story = {
  play: async ({ args, canvasElement }) => {
    const canvas = within(canvasElement);
    const bulgariaButton = canvas.getByRole("button", { name: "Bulgaria" });
    await userEvent.click(bulgariaButton);
    const holdButton = canvas.getByRole("button", { name: "Hold" });
    await userEvent.click(holdButton);
    const button = canvas.getByRole("button", { name: "Save" });
    await userEvent.click(button);
    expect(args.onSubmit).toHaveBeenCalled();
  },
};
