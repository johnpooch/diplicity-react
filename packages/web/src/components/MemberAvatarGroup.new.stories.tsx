import type { Meta, StoryObj } from "@storybook/react";
import { MemberAvatarGroup } from "./MemberAvatarGroup.new";
import { MemberRead } from "../store";

const meta = {
  title: "Components/MemberAvatarGroup",
  component: MemberAvatarGroup,
  parameters: {
    layout: "centered",
  },
} satisfies Meta<typeof MemberAvatarGroup>;

export default meta;
type Story = StoryObj<typeof meta>;

const createMember = (member: {
  id: number;
  nation: string;
  isCurrentUser?: boolean;
}) =>
  ({
    ...member,
    name: `Player ${member.id}`,
    picture: null,
    isCurrentUser: member.isCurrentUser ?? false,
  }) as MemberRead;

const mockMembers = [
  createMember({
    id: 1,
    nation: "austria",
  }),
  createMember({
    id: 2,
    nation: "england",
  }),
  createMember({
    id: 3,
    nation: "france",
  }),
  createMember({
    id: 4,
    nation: "germany",
  }),
  createMember({
    id: 5,
    nation: "italy",
  }),
  createMember({
    id: 6,
    nation: "russia",
  }),
  createMember({
    id: 7,
    nation: "turkey",
  }),
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
        createMember({
          id: 1,
          nation: "austria",
        }),
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
      members: [
        createMember({
          id: 1,
          nation: "austria",
        }),
        createMember({
          id: 3,
          nation: "france",
        }),
      ],
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
