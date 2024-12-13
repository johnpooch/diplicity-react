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
        status: "active",
        variant: "Classical",
        phaseDuration: "24h",
        private: false,
        canJoin: false,
        canLeave: false,
        onClickGameInfo: () => alert('Game info clicked!'),
        onClickPlayerInfo: () => alert('Player info clicked!'),
        onClickShare: () => alert('Share clicked!'),
        onClickJoin: () => alert('Join clicked!'),
        onClickLeave: () => alert('Leave clicked!'),
    }
} satisfies Meta<typeof GameCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const StagingGameUserCanJoin: Story = {
    args: {
        id: '5',
        title: 'Staging Game you can join',
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'staging',
        canJoin: true,
    }
};

export const StagingGameUserCantJoin: Story = {
    args: {
        id: '6',
        title: 'Staging Game you can\'t join',
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'staging',
        canJoin: false,
        private: true,
    }
};

export const StagingGameUserHasJoined: Story = {
    args: {
        id: '7',
        title: 'Staging Game you have joined',
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'staging',
        canJoin: false,
        canLeave: true,
    }
};

export const ActiveGameUserNotMember: Story = {
    args: {
        id: '8',
        title: 'Active Game you are not a member of',
        timeLeft: "6 hours",
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'active',
        canJoin: false,
    }
};

export const ActiveGameUserIsMember: Story = {
    args: {
        id: '9',
        title: 'Active Game you are a member of',
        users: PlayerAvatarStackStories.Default.args?.users,
        timeLeft: "6 hours",
        status: 'active',
        canJoin: false,
        canLeave: true,
    }
};

export const ActiveGameNoOrdersReceived: Story = {
    args: {
        id: '10',
        title: 'Active Game you are a member of with no orders received',
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'active',
        timeLeft: "6 hours",
        canJoin: false,
        canLeave: true,
        ordersStatus: "pending"
    }
};

export const ActiveGameOrdersReceivedNotConfirmed: Story = {
    args: {
        id: '11',
        title: 'Active Game you are a member of with orders received',
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'active',
        timeLeft: "6 hours",
        canJoin: false,
        canLeave: true,
        ordersStatus: "unconfirmed"
    }
};

export const ActiveGameOrdersReceivedConfirmed: Story = {
    args: {
        id: '12',
        title: 'Active Game you are a member of with orders received and confirmed',
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'active',
        timeLeft: "6 hours",
        canJoin: false,
        canLeave: true,
        ordersStatus: "confirmed"
    }
};

export const ActiveGameMissedOrdersWarning: Story = {
    args: {
        id: '13',
        title: 'Active Game you are a member of with missed orders warning',
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'active',
        canJoin: false,
        canLeave: true,
        timeLeft: "6 hours",
        ordersStatus: "missed"
    }
};

export const FinishedGame: Story = {
    args: {
        id: '14',
        title: 'Finished Game',
        users: PlayerAvatarStackStories.Default.args?.users,
        status: 'finished',
    }
};
