import type { Meta, StoryObj } from '@storybook/react';
import BrowseGames from './BrowseGames';
import * as GameCardStories from '../components/GameCard.stories';
import GameCardDefault from '../components/GameCard.stories';

const meta = {
    title: 'Pages/BrowseGames',
    component: BrowseGames,
    parameters: {
        layout: 'centered',
    },
} satisfies Meta<typeof BrowseGames>;

const link = 'https://example.com';

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        games: [
            { ...GameCardDefault.args, ...GameCardStories.NoUsers.args, link },
            { ...GameCardDefault.args, ...GameCardStories.UserOverflow.args, link },
            { ...GameCardDefault.args, ...GameCardStories.NoUsers.args, link },
            { ...GameCardDefault.args, ...GameCardStories.UserOverflow.args, link },
            { ...GameCardDefault.args, ...GameCardStories.NoUsers.args, link },
            { ...GameCardDefault.args, ...GameCardStories.UserOverflow.args, link }
        ]
    },
};