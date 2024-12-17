import type { Meta, StoryObj } from '@storybook/react';
import { HomeScreen } from './HomeScreen';
import { withRouterDecorator } from '../storybook';
import { useHomeQuery } from '../common';


const meta = {
    title: 'Pages/HomeScreen',
    component: HomeScreen,
    decorators: [withRouterDecorator],
    args: {
        gameCallbacks: {
            onClickGameInfo: () => { },
            onClickPlayerInfo: () => { },
            onClickShare: () => { },
            onClickJoin: () => { },
            onClickLeave: () => { },
        }
    }
} satisfies Meta<typeof HomeScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

const loadingQuery: ReturnType<typeof useHomeQuery> = ({
    data: undefined,
    isLoading: true,
    isSuccess: false,
    isError: false,
});

export const LoadingSmallMobile: Story = {
    args: {
        useHomeQuery: () => loadingQuery
    },
    parameters: {
        viewport: {
            defaultViewport: 'mobile1',
        },
    },
};

export const LoadingLargeMobile: Story = {
    args: {
        useHomeQuery: () => loadingQuery
    },
    parameters: {
        viewport: {
            defaultViewport: 'mobile2',
        },
    },
};

export const LoadingTablet: Story = {
    args: {
        useHomeQuery: () => loadingQuery
    },
    parameters: {
        viewport: {
            defaultViewport: 'tablet',
        },
    },
};