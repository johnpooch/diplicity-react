import type { Meta, StoryObj } from "@storybook/react";
import { RemainingTimeDisplay } from "./RemainingTimeDisplay";

const meta = {
  title: "Components/RemainingTimeDisplay",
  component: RemainingTimeDisplay,
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
} satisfies Meta<typeof RemainingTimeDisplay>;

export default meta;
type Story = StoryObj<typeof meta>;

export const LessThanOneMinute: Story = {
  args: {
    remainingTime: 30,
    scheduledResolution: new Date(Date.now() + 30000).toISOString(),
  },
};

export const ThirtyMinutes: Story = {
  args: {
    remainingTime: 1800,
    scheduledResolution: new Date(Date.now() + 1800000).toISOString(),
  },
};

export const FiveHours: Story = {
  args: {
    remainingTime: 19800,
    scheduledResolution: new Date(Date.now() + 19800000).toISOString(),
  },
};

export const TwoDays: Story = {
  args: {
    remainingTime: 172800,
    scheduledResolution: new Date(Date.now() + 172800000).toISOString(),
  },
};

export const DeadlinePassed: Story = {
  args: {
    remainingTime: 0,
    scheduledResolution: new Date(Date.now() - 60000).toISOString(),
  },
};
