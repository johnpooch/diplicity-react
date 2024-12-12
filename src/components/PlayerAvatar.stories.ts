import type { Meta, StoryObj } from '@storybook/react';
import PlayerAvatar from './PlayerAvatar';

const meta = {
    title: 'Components/PlayerAvatar',
    component: PlayerAvatar,
    parameters: {
        layout: 'centered',
    },
} satisfies Meta<typeof PlayerAvatar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        username: 'JohnDoe',
        onClick: () => alert('Avatar clicked!'),
    },
};