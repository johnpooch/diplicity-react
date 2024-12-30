import type { Meta, StoryObj } from "@storybook/react";
import { fn } from "@storybook/test";
import { CreateOrder } from "./CreateOrder";

const defaultUseCreateOrder = {
  handleSelect: fn(),
  handleBack: fn(),
  handleClose: fn(),
  handleSubmit: fn(),
  order: {
    isComplete: false,
  },
  isSubmitting: false,
} as const;

const meta: Meta<typeof CreateOrder> = {
  title: "Components/CreateOrderNew",
  component: CreateOrder,
  parameters: {
    layout: "fullscreen",
    viewport: {
      defaultViewport: "mobile1",
    },
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Loading: Story = {
  args: {
    useCreateOrder: () => ({
      isLoading: true,
    }),
  },
};

export const SelectUnit: Story = {
  args: {
    useCreateOrder: () => ({
      ...defaultUseCreateOrder,
      activeStep: 0,
      options: {
        bul: { name: "Bulgaria", children: {} },
        con: { name: "Constantinople", children: {} },
      },
    }),
  },
};

export const SelectOrderType: Story = {
  args: {
    useCreateOrder: () => ({
      ...defaultUseCreateOrder,
      activeStep: 1,
      options: {
        Hold: { name: "Hold", children: {} },
        Move: { name: "Move", children: {} },
      },
      order: {
        ...defaultUseCreateOrder.order,
        source: { name: "Bulgaria", children: {} },
      },
    }),
  },
};

export const SelectTarget: Story = {
  args: {
    useCreateOrder: () => ({
      ...defaultUseCreateOrder,
      activeStep: 2,
      options: {
        con: { name: "Constantinople", children: {} },
        gal: { name: "Galicia", children: {} },
      },
      order: {
        ...defaultUseCreateOrder.order,
        source: { name: "Bulgaria", children: {} },
        orderType: { name: "Move", children: {} },
      },
    }),
  },
};

export const SelectAux: Story = {
  args: {
    useCreateOrder: () => ({
      ...defaultUseCreateOrder,
      activeStep: 3,
      options: {
        con: { name: "Constantinople", children: {} },
        gal: { name: "Galicia", children: {} },
      },
      order: {
        ...defaultUseCreateOrder.order,
        source: { name: "Bulgaria", children: {} },
        orderType: { name: "Support", children: {} },
        target: { name: "Constantinople", children: {} },
      },
    }),
  },
};

export const ConfirmHold: Story = {
  args: {
    useCreateOrder: () => ({
      ...defaultUseCreateOrder,
      activeStep: 2,
      options: {},
      order: {
        ...defaultUseCreateOrder.order,
        source: { name: "Bulgaria", children: {} },
        orderType: { name: "Hold", children: {} },
        isComplete: true,
      },
    }),
  },
};

export const ConfirmMove: Story = {
  args: {
    useCreateOrder: () => ({
      ...defaultUseCreateOrder,
      activeStep: 3,
      options: {},
      order: {
        ...defaultUseCreateOrder.order,
        source: { name: "Bulgaria", children: {} },
        orderType: { name: "Move", children: {} },
        target: { name: "Constantinople", children: {} },
        isComplete: true,
      },
    }),
  },
};

export const ConfirmSupport: Story = {
  args: {
    useCreateOrder: () => ({
      ...defaultUseCreateOrder,
      activeStep: 4,
      options: {},
      order: {
        ...defaultUseCreateOrder.order,
        source: { name: "Bulgaria", children: {} },
        orderType: { name: "Support", children: {} },
        target: { name: "Constantinople", children: {} },
        aux: { name: "Galicia", children: {} },
        isComplete: true,
      },
    }),
  },
};
