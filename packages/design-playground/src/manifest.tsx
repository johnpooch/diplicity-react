import type { ReactNode } from "react";
import { SingleList } from "@/prototypes/my-games/SingleList";
import { GroupedByPhase } from "@/prototypes/my-games/GroupedByPhase";
import { CreateGame } from "@/prototypes/create-game/Default";
import { PlayerProfile } from "@/prototypes/player-profile/Default";
import { Channel } from "@/prototypes/channel/Default";
import { CardGallery } from "@/prototypes/card-gallery/Default";
import { Gallery as VariantCardGallery } from "@/prototypes/variant-card/Gallery";
import { VariantDetail } from "@/prototypes/variant-detail/Default";
import { Gallery as PlayerCardGallery } from "@/prototypes/player-card/Gallery";
import { Member as PlayerCardMember } from "@/prototypes/player-card/Member";
import { GameInfo } from "@/prototypes/game-info/StackedSections";
import { PlayersList } from "@/prototypes/players-list/GameFocused";
import { ChatChannelList } from "@/prototypes/chat-channel-list/SingleList";
import { CreateChannel } from "@/prototypes/create-channel/SingleForm";
import { ChatChannel } from "@/prototypes/chat-channel/NationBubbles";
import { CurrentPhaseOrdersList } from "@/prototypes/current-phase-orders/YourList";
import { NoOrdersRequired } from "@/prototypes/current-phase-orders/NoOrdersRequired";
import { AllConfirmed } from "@/prototypes/current-phase-orders/AllConfirmed";

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
  {
    slug: "variant-card",
    title: "Variant Card",
    description:
      "The variant preview on game info. Press opens the variant detail screen.",
    variants: [
      {
        slug: "thumbnail-row",
        title: "Thumbnail row",
        description:
          "Map thumbnail, two-line clamped description and a chevron. The rest of the variant lives on a separate screen.",
        states: [defaultState],
        render: () => <VariantCardGallery />,
      },
    ],
  },
  {
    slug: "variant-detail",
    title: "Variant Detail",
    description: "The full variant, reached by pressing the variant card.",
    variants: [
      {
        slug: "full-page",
        title: "Full page",
        description: "Title, map and the untruncated description.",
        states: [
          { slug: "sengoku", title: "Sengoku" },
          { slug: "classical", title: "Classical" },
          { slug: "unconstitutional", title: "Unconstitutional" },
        ],
        render: state => <VariantDetail state={state} />,
      },
    ],
  },
  {
    slug: "player-card",
    title: "Player Card",
    description:
      "A player in a game. On the players list it opens the member screen; on the member screen it opens the profile.",
    variants: [
      {
        slug: "all-states",
        title: "All states",
        description:
          "Identity-first before the game starts, nation-first once it has. Preferred nations are a dashed flag; assigned nations are solid.",
        states: [defaultState],
        render: () => <PlayerCardGallery />,
      },
      {
        slug: "member-destination",
        title: "On the member screen",
        description:
          "The same card, now as a link to the player profile.",
        states: [defaultState],
        render: () => <PlayerCardMember />,
      },
    ],
  },
  {
    slug: "game-info",
    title: "Game Info",
    description: "The info tab of a game.",
    variants: [
      {
        slug: "stacked-sections",
        title: "Stacked sections",
        description:
          "Variant, deadlines and settings as stacked sections. The variant is a compact card that opens variant details.",
        states: [
          { slug: "pending", title: "Pending" },
          { slug: "no-extensions", title: "No extensions" },
          { slug: "private", title: "Private" },
          { slug: "high-commitment", title: "High commitment" },
          { slug: "gunboat", title: "Gunboat" },
          { slug: "private-gunboat", title: "Private gunboat" },
          { slug: "joined", title: "Joined" },
        ],
        render: state => <GameInfo state={state} />,
      },
    ],
  },
  {
    slug: "players-list",
    title: "Players List",
    description:
      "The players tab of a game. Game-focused: identity before it starts, nation once it has.",
    variants: [
      {
        slug: "game-focused",
        title: "Game focused",
        description:
          "Identity-first while the game is forming, nation-first once it is underway. Finished games become a results screen. A non-playing game master sits above the players when present. Tap opens the member screen.",
        states: [
          { slug: "pending-member", title: "Pending (member)" },
          { slug: "pending-member-gm", title: "Pending (member, GM)" },
          { slug: "pending-non-member", title: "Pending (non-member)" },
          { slug: "mustering", title: "Mustering" },
          { slug: "mustering-gm", title: "Mustering (GM)" },
          { slug: "active", title: "Active" },
          { slug: "active-gm", title: "Active (GM)" },
          { slug: "active-eliminated", title: "Active (eliminated)" },
          { slug: "active-anon", title: "Active (anonymous)" },
          { slug: "solo-victory", title: "Solo victory" },
          { slug: "solo-victory-gm", title: "Solo victory (GM)" },
          { slug: "draw", title: "Draw" },
        ],
        render: state => <PlayersList state={state} />,
      },
    ],
  },
  {
    slug: "chat-channel-list",
    title: "Chat Channel List",
    description: "The chat tab of a game. Public Press is always present.",
    variants: [
      {
        slug: "single-list",
        title: "Single list",
        description:
          "One flat list. Public Press is named, not chipped. Create lives in the header once the game has started.",
        states: [
          { slug: "active", title: "Active" },
          { slug: "pending", title: "Pending" },
        ],
        render: state => <ChatChannelList state={state} />,
      },
    ],
  },
  {
    slug: "create-channel",
    title: "Create Channel",
    description:
      "A secondary screen. Pick members and optionally name the channel.",
    variants: [
      {
        slug: "single-form",
        title: "Single form",
        description:
          "Members and an optional name on one screen. Secondary chrome: back replaces home, the mobile tab bar is gone, the desktop rail stays.",
        states: [defaultState],
        render: () => <CreateChannel />,
      },
    ],
  },
  {
    slug: "chat-channel",
    title: "Chat Channel",
    description:
      "A secondary screen. A press channel inside a game, reached from the chat list.",
    variants: [
      {
        slug: "nation-bubbles",
        title: "Nation bubbles",
        description:
          "Secondary chrome: back replaces home, the mobile tab bar is gone, the desktop rail stays. Nation-coloured bubbles; yours on the right. Phase changes sit in the stream.",
        states: [
          { slug: "empty", title: "Direct, no messages" },
          { slug: "one", title: "Direct, one message" },
          { slug: "direct", title: "Direct, many messages" },
          { slug: "group-one", title: "Group, one message" },
          { slug: "group", title: "Group, many messages" },
        ],
        render: state => <ChatChannel state={state} />,
      },
    ],
  },
  {
    slug: "current-phase-orders",
    title: "Current Phase Orders",
    description:
      "The orders tab while the phase is still open. Only your orders are visible.",
    variants: [
      {
        slug: "your-list",
        title: "Your list",
        description:
          "Your units as a card list. Phase name and remaining time replace the title; the phase list sits in the header; confirm and progress share one button.",
        states: [
          { slug: "incomplete", title: "Incomplete" },
          { slug: "confirmed", title: "Confirmed" },
          { slug: "no-orders", title: "No orders required" },
          { slug: "civil-disorder", title: "Civil disorder" },
          { slug: "spectator", title: "Spectator" },
          { slug: "sandbox", title: "Sandbox" },
          { slug: "retreat", title: "Retreat" },
          { slug: "adjustment", title: "Adjustment" },
        ],
        render: state => <CurrentPhaseOrdersList state={state} />,
      },
      {
        slug: "no-orders-required",
        title: "No orders required",
        description:
          "When nothing is orderable, keep nation and phase chrome and say why. No confirm button, no tab badge.",
        states: [
          { slug: "retreat", title: "Retreat" },
          { slug: "adjustment", title: "Adjustment" },
          { slug: "movement", title: "Movement" },
        ],
        render: state => <NoOrdersRequired state={state} />,
      },
      {
        slug: "all-confirmed",
        title: "All confirmed",
        description:
          "Every slot has an order and you have confirmed. The tab is quiet; the button is an outline you can tap to unconfirm.",
        states: [
          { slug: "movement", title: "Movement" },
          { slug: "retreat", title: "Retreat" },
          { slug: "adjustment", title: "Adjustment" },
        ],
        render: state => <AllConfirmed state={state} />,
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
