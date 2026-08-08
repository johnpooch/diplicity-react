import type { ReactNode } from "react";
import { SingleList } from "@/prototypes/my-games/SingleList";
import { GroupedByPhase } from "@/prototypes/my-games/GroupedByPhase";
import { CreateGame } from "@/prototypes/create-game/Default";
import { PlayerProfile } from "@/prototypes/player-profile/Default";
import { Channel } from "@/prototypes/channel/Default";
import { CardGallery } from "@/prototypes/card-gallery/Default";

export interface PrototypeState {
  slug: string;
  title: string;
}

export interface PrototypeVariant {
  slug: string;
  title: string;
  description: string;
  states: PrototypeState[];
  render: (state: string) => ReactNode;
}

export interface Prototype {
  slug: string;
  title: string;
  description: string;
  variants: PrototypeVariant[];
}

const defaultState: PrototypeState = { slug: "default", title: "Default" };

export const prototypes: Prototype[] = [
  {
    slug: "my-games",
    title: "My Games",
    description: "The list of games you are currently in.",
    variants: [
      {
        slug: "single-list",
        title: "Single list",
        description:
          "One flat list ordered by deadline. Status lives on the card.",
        states: [
          defaultState,
          { slug: "empty", title: "No games" },
          { slug: "many", title: "Many games" },
        ],
        render: state => <SingleList state={state} />,
      },
      {
        slug: "grouped-by-phase",
        title: "Grouped by phase",
        description:
          "Split into what needs you, what is waiting on others, staging and finished.",
        states: [
          defaultState,
          { slug: "empty", title: "No games" },
          { slug: "many", title: "Many games" },
        ],
        render: state => <GroupedByPhase state={state} />,
      },
    ],
  },
  {
    slug: "create-game",
    title: "Create Game",
    description: "Setting up a new game, including filling seats with bots.",
    variants: [
      {
        slug: "bot-seat-counter",
        title: "Bot seat counter",
        description:
          "Bots are a number of seats rather than individually chosen opponents.",
        states: [
          defaultState,
          { slug: "with-bots", title: "Three bots selected" },
        ],
        render: state => <CreateGame state={state} />,
      },
    ],
  },
  {
    slug: "player-profile",
    title: "Player Profile",
    description: "How a player's record and statistics are presented.",
    variants: [
      {
        slug: "stat-grid",
        title: "Stat grid",
        description:
          "Headline numbers in a grid, then most-played nation and recent results.",
        states: [defaultState],
        render: () => <PlayerProfile />,
      },
    ],
  },
  {
    slug: "channel",
    title: "Chat Channel",
    description: "A press channel inside a game.",
    variants: [
      {
        slug: "bubbles",
        title: "Bubbles",
        description:
          "Messages as bubbles with nation avatars; your own messages right-aligned.",
        states: [defaultState, { slug: "empty", title: "No messages" }],
        render: state => <Channel state={state} />,
      },
    ],
  },
  {
    slug: "card-gallery",
    title: "Game Card Gallery",
    description:
      "Every state a game card can be in, on one page. Moved out of the production app.",
    variants: [
      {
        slug: "all-states",
        title: "All states",
        description: "Twelve scenarios stacked vertically.",
        states: [defaultState],
        render: () => <CardGallery />,
      },
    ],
  },
];

export const findVariant = (
  prototypeSlug?: string,
  variantSlug?: string
): { prototype: Prototype; variant: PrototypeVariant } | undefined => {
  const prototype = prototypes.find(item => item.slug === prototypeSlug);
  const variant = prototype?.variants.find(item => item.slug === variantSlug);
  return prototype && variant ? { prototype, variant } : undefined;
};
