import type { Meta, StoryObj } from '@storybook/react';
import { PlayerInfoCard } from './PlayerInfoCard';
import { withRouterDecorator } from '../storybook';

const meta = {
    title: 'Components/PlayerInfoCard',
    component: PlayerInfoCard,
    decorators: [withRouterDecorator],
    args: {
        id: "1",
        src: "https://via.placeholder.com/150",
        username: "John Doe",
        stats: {
            numPlayed: 10,
            numWon: 5,
            numDrawn: 3,
            numAbandoned: 2,
            consistency: "Consistent",
            rank: "Private first class",
        }
    },
} satisfies Meta<typeof PlayerInfoCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
