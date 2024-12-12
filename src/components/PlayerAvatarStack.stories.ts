import type { Meta, StoryObj } from '@storybook/react';
import PlayerAvatarStack from './PlayerAvatarStack';

const meta = {
    title: 'Components/PlayerAvatarStack',
    component: PlayerAvatarStack,
    parameters: {
        layout: 'centered',
    },
    args: {
        onClick: () => alert('Stack clicked!'),
    }
} satisfies Meta<typeof PlayerAvatarStack>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        users: [
            { username: 'Alice' },
            { username: 'Bob' },
            { username: 'Charlie' },
        ],
    },
};

export const MaxAvatars: Story = {
    args: {
        users: [
            { username: 'Alice' },
            { username: 'Bob' },
            { username: 'Charlie' },
            { username: 'David' },
            { username: 'Eve' },
            { username: 'Frank' },
            { username: 'Grace' },
        ],
    },
};

export const OverflowAvatars: Story = {
    args: {
        users: [
            { username: 'Alice' },
            { username: 'Bob' },
            { username: 'Charlie' },
            { username: 'David' },
            { username: 'Eve' },
            { username: 'Frank' },
            { username: 'Grace' },
            { username: 'Hank' },
            { username: 'Ivy' },
        ],
    },
};