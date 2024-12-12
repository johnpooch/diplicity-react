import type { Meta, StoryObj } from '@storybook/react';
import StatusChip from './StatusChip';

const meta = {
    title: 'Components/StatusChip',
    component: StatusChip,
    parameters: {
        layout: 'centered',
    },
} satisfies Meta<typeof StatusChip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Confirmed: Story = {
    args: {
        status: 'confirmed',
        label: 'Orders confirmed',
    },
};

export const Pending: Story = {
    args: {
        status: 'pending',
        label: 'Orders pending',
    },
};

export const Unconfirmed: Story = {
    args: {
        status: 'unconfirmed',
        label: 'Orders unconfirmed',
    },
};

export const Missed: Story = {
    args: {
        status: 'missed',
        label: 'Orders missed',
    },
};