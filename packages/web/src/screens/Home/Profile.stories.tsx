import type { Meta, StoryObj } from "@storybook/react";
import { Profile } from "./Profile";
import { getUserRetrieveMockHandler } from "@/api/generated/endpoints";
import { mockUserProfile } from "@/mocks";
import { withHomeLayout } from "@/stories/decorators";

const meta = {
  title: "Screens/Home/Profile",
  component: Profile,
  decorators: [withHomeLayout],
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
