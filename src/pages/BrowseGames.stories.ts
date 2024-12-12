import type { Meta, StoryObj } from '@storybook/react';
import BrowseGames from './BrowseGames';

const meta = {
    title: 'Pages/BrowseGames',
    component: BrowseGames,
    parameters: {
        layout: 'centered',
    },
} satisfies Meta<typeof BrowseGames>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {},
};