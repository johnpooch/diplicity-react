import type { Meta, StoryObj } from '@storybook/react';
import { GameInfo } from './GameInfo';
import { withRouterDecorator } from '../storybook';

const meta = {
    title: 'Components/GameInfo',
    component: GameInfo,
    decorators: [withRouterDecorator],
    args: {
        gameId: "1",
        useGameInfoQuery: () => ({
            isLoading: false,
            isSuccess: true,
            isError: false,
            data: {
                variant: "Classic",
                movementPhaseDuration: "24 hours",
                nonMovementPhaseDuration: "24 hours",
                minCommitment: "Committed",
                minRank: "Private first class",
                maxRank: "General",
                language: "English"
            },
        }),
    },
} satisfies Meta<typeof GameInfo>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
