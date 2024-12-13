import type { Meta, StoryObj } from '@storybook/react';
import GameCardSkeleton from './GameCardSkeleton';

const meta = {
    title: 'Components/GameCardSkeleton',
    component: GameCardSkeleton,
    parameters: {
        layout: 'centered',
    },
} satisfies Meta<typeof GameCardSkeleton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};