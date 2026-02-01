import type { Meta, StoryObj } from "@storybook/react";
import { Community } from "./Community";
import { getUserRetrieveMockHandler } from "@/api/generated/endpoints";
import { mockUserProfile } from "@/mocks";
import { withHomeLayout } from "@/stories/decorators";

const meta = {
  title: "Screens/Home/Community",
  component: Community,
  decorators: [withHomeLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/community",
      initialEntries: ["/community"],
    },
    msw: {
      handlers: [getUserRetrieveMockHandler(mockUserProfile)],
    },
  },
} satisfies Meta<typeof Community>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
