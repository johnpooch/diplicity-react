import type { Meta, StoryObj } from '@storybook/react';
import MyGames from './MyGames';
import * as GameCardStories from '../components/GameCard.stories';
import GameCardDefault from '../components/GameCard.stories';

const meta = {
    title: 'Pages/MyGames',
    component: MyGames,
    parameters: {
        layout: 'centered',
    },
} satisfies Meta<typeof MyGames>;

const link = 'https://example.com';

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        games: [
            { ...GameCardDefault.args, ...GameCardStories.StagingGameUserCanJoin.args, link },
        ]
    },
};