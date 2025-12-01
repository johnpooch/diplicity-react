import type { Meta, StoryObj } from "@storybook/react";
import { MemberAvatarGroup } from "./MemberAvatarGroup.new";

const meta = {
  title: "Components/MemberAvatarGroup",
  component: MemberAvatarGroup,
  parameters: {
    layout: "centered",
  },
} satisfies Meta<typeof MemberAvatarGroup>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockMembers = [
  {
    id: 1,
    name: "Player 1",
    picture: null,
    nation: "austria",
    isCurrentUser: false,
  },
  {
    id: 2,
    name: "Player 2",
    picture: null,
    nation: "england",
    isCurrentUser: false,
  },
  {
    id: 3,
    name: "Player 3",
    picture: null,
    nation: "france",
    isCurrentUser: false,
  },
  {
    id: 4,
    name: "Player 4",
    picture: null,
    nation: "germany",
    isCurrentUser: false,
  },
  {
    id: 5,
    name: "Player 5",
    picture: null,
    nation: "italy",
    isCurrentUser: false,
  },
  {
    id: 6,
    name: "Player 6",
    picture: null,
    nation: "russia",
    isCurrentUser: false,
  },
  {
    id: 7,
    name: "Player 7",
    picture: null,
    nation: "turkey",
    isCurrentUser: false,
  },
];

export const Small: Story = {
  args: {
    members: mockMembers.slice(0, 4),
    variant: "classical",
    size: "small",
  },
};

export const Medium: Story = {
  args: {
    members: mockMembers.slice(0, 4),
    variant: "classical",
    size: "medium",
  },
};

export const WithWinner: Story = {
  args: {
    members: mockMembers.slice(0, 4),
    variant: "classical",
    size: "medium",
    victory: {
      members: [
        {
          id: 2,
          name: "Player 2",
          picture: null,
          nation: "england",
          isCurrentUser: false,
        },
      ],
    },
  },
};

export const WithMultipleWinners: Story = {
  args: {
    members: mockMembers.slice(0, 4),
    variant: "classical",
    size: "medium",
    victory: {
      members: [{ id: 1 }, { id: 3 }],
    },
  },
};

export const MaxSevenMembers: Story = {
  args: {
    members: mockMembers,
    variant: "classical",
    size: "medium",
  },
};

export const OverflowWithPlus: Story = {
  args: {
    members: [
      ...mockMembers,
      {
        id: 8,
        name: "Player 8",
        picture: null,
        nation: "austria",
        isCurrentUser: false,
      },
      {
        id: 9,
        name: "Player 9",
        picture: null,
        nation: "england",
        isCurrentUser: false,
      },
    ],
    variant: "classical",
    size: "medium",
    max: 5,
  },
};
