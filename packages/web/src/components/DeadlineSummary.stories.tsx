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

// Duration Mode Stories
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
  name: "Different Retreat Duration",
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

// Fixed-Time Mode Stories
export const FixedTimeDaily: Story = {
  name: "Fixed-Time: Daily",
  args: {
    movementPhaseDuration: null,
    deadlineMode: "fixed_time",
    fixedDeadlineTime: "21:00",
    fixedDeadlineTimezone: "America/New_York",
    movementFrequency: "daily",
  },
};

export const FixedTimeHourly: Story = {
  name: "Fixed-Time: Hourly",
  args: {
    movementPhaseDuration: null,
    deadlineMode: "fixed_time",
    fixedDeadlineTime: "14:30",
    fixedDeadlineTimezone: "America/Chicago",
    movementFrequency: "hourly",
  },
};

export const FixedTimeEvery2Days: Story = {
  name: "Fixed-Time: Every 2 Days",
  args: {
    movementPhaseDuration: null,
    deadlineMode: "fixed_time",
    fixedDeadlineTime: "18:00",
    fixedDeadlineTimezone: "Europe/Berlin",
    movementFrequency: "every_2_days",
  },
};

export const FixedTimeWeekly: Story = {
  name: "Fixed-Time: Weekly",
  args: {
    movementPhaseDuration: null,
    deadlineMode: "fixed_time",
    fixedDeadlineTime: "15:00",
    fixedDeadlineTimezone: "America/Los_Angeles",
    movementFrequency: "weekly",
  },
};

export const FixedTimeDifferentRetreat: Story = {
  name: "Fixed-Time: Different Retreat Frequency",
  args: {
    movementPhaseDuration: null,
    deadlineMode: "fixed_time",
    fixedDeadlineTime: "21:00",
    fixedDeadlineTimezone: "Europe/London",
    movementFrequency: "daily",
    retreatFrequency: "hourly",
  },
};

export const FixedTimeIncomplete: Story = {
  name: "Fixed-Time: Incomplete (Prompt)",
  args: {
    movementPhaseDuration: null,
    deadlineMode: "fixed_time",
    fixedDeadlineTime: "21:00",
    fixedDeadlineTimezone: null,
    movementFrequency: null,
  },
};

export const FixedTimeUTC: Story = {
  name: "Fixed-Time: UTC",
  args: {
    movementPhaseDuration: null,
    deadlineMode: "fixed_time",
    fixedDeadlineTime: "12:00",
    fixedDeadlineTimezone: "UTC",
    movementFrequency: "daily",
  },
};

export const FixedTimeMidnight: Story = {
  name: "Fixed-Time: Midnight",
  args: {
    movementPhaseDuration: null,
    deadlineMode: "fixed_time",
    fixedDeadlineTime: "00:00",
    fixedDeadlineTimezone: "America/New_York",
    movementFrequency: "daily",
  },
};
