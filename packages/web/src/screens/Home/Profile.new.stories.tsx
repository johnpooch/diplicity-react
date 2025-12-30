import type { Meta, StoryObj } from "@storybook/react";
import { Profile } from "./Profile.new";
import { getUserRetrieveMockHandler } from "@/api/generated/endpoints";
import { mockUserProfile } from "@/mocks";
import { HomeLayout } from "../../components/HomeLayout";

const meta = {
  title: "Screens/Profile",
  component: Profile,
  render: args => (
    <HomeLayout>
      <Profile {...args} />
    </HomeLayout>
  ),
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/profile",
      initialEntries: ["/profile"],
    },
    msw: {
      handlers: [getUserRetrieveMockHandler(mockUserProfile)],
    },
  },
} satisfies Meta<typeof Profile>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithAvatar: Story = {
  parameters: {
    msw: {
      handlers: [
        getUserRetrieveMockHandler({
          ...mockUserProfile,
          name: "Jane Doe",
          picture: "https://i.pravatar.cc/150?img=5",
        }),
      ],
    },
  },
};

export const NotificationsEnabled: Story = {
  parameters: {
    messaging: {
      enabled: true,
      permissionDenied: false,
      error: null,
      isLoading: false,
    },
  },
};

export const NotificationsError: Story = {
  parameters: {
    messaging: {
      enabled: false,
      permissionDenied: false,
      error: "Failed to register service worker",
      isLoading: false,
    },
  },
};
