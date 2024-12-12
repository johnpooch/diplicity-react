import type { Meta, StoryObj } from '@storybook/react';
import GameCard from './GameCard';
import * as PlayerAvatarStackStories from './PlayerAvatarStack.stories';

const meta = {
    title: 'Components/GameCard',
    component: GameCard,
    parameters: {
        layout: 'centered',
    },
    args: {
        onClickGameInfo: () => alert('Game info clicked!'),
        onClickPlayerInfo: () => alert('Player info clicked!'),
        onClickShare: () => alert('Share clicked!'),
    }
} satisfies Meta<typeof GameCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const NoUsers: Story = {
    args: {
        id: '1',
        title: 'Game with no users',
        users: []
    },
};

export const UserOverflow: Story = {
    args: {
        id: '2',
        title: 'Game with more than 7 users',
        users: PlayerAvatarStackStories.OverflowAvatars.args?.users,
    }
};
