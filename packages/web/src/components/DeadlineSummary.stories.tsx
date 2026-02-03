import type { Meta, StoryObj } from "@storybook/react";
import { DeadlineSummary } from "./DeadlineSummary";

const meta = {
  title: "Components/DeadlineSummary",
  component: DeadlineSummary,
  parameters: {
    layout: "centered",
  },
  decorators: [
    Story => (
      <div className="p-4 text-sm text-muted-foreground">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof DeadlineSummary>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    movementPhaseDuration: "24 hours",
  },
};

export const OneHour: Story = {
  args: {
    movementPhaseDuration: "1 hour",
  },
};

export const TwelveHours: Story = {
  args: {
    movementPhaseDuration: "12 hours",
  },
};

export const FortyEightHours: Story = {
  args: {
    movementPhaseDuration: "48 hours",
  },
};

export const ThreeDays: Story = {
  args: {
    movementPhaseDuration: "3 days",
  },
};

export const OneWeek: Story = {
  args: {
    movementPhaseDuration: "1 week",
  },
};

export const TwoWeeks: Story = {
  args: {
    movementPhaseDuration: "2 weeks",
  },
};

export const Sandbox: Story = {
  name: "Sandbox (No Deadlines)",
  args: {
    movementPhaseDuration: null,
  },
};

export const DifferentRetreatDuration: Story = {
  name: "Different Retreat Duration (Future)",
  args: {
    movementPhaseDuration: "48 hours",
    retreatPhaseDuration: "12 hours",
  },
};

export const SameRetreatDuration: Story = {
  name: "Same Retreat Duration",
  args: {
    movementPhaseDuration: "24 hours",
    retreatPhaseDuration: "24 hours",
  },
};
