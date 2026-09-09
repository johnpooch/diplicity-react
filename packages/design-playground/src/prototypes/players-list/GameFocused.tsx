import { Button } from "@/components/ui/button";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GameDetailShell } from "@/components/GameDetailShell";
import { AddPlayerCard, PlayerCard } from "@/components/PlayerCard";
import { cn } from "@/lib/utils";
import {
  janeDoe,
  janeDoeActive,
  janeDoeAnon,
  janeDoeDraw,
  janeDoeEliminated,
  janeDoeMustering,
  johnDoeActive,
  johnDoeAnon,
  johnDoeDraw,
  johnDoeMustering,
  johnDoeNoPreferences,
  johnDoeSolo,
  theChancellor,
  theChancellorActive,
  theChancellorEliminated,
  theChancellorMustering,
  wilhelmina,
  wilhelminaEliminated,
  wilhelminaFormer,
  zaraGameMaster,
} from "@/data/fixtures";
import type { Player, PlayerCardPresentation } from "@/data/types";
import {
  Check,
  ChevronDown,
  Send,
  Share2,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

const memberPath = "/player-card/member-destination";
const profilePath = "/player-profile/stat-grid";

const seated = (player: Player): Player =>
  player.role === "admin" ? { ...player, role: undefined } : player;

type HeaderExtra = "add" | "join" | "confirm";

interface ListAction {
  label: string;
  icon: LucideIcon;
}

interface ScreenConfig {
  title: string;
  players: Player[];
  gameMaster?: Player;
  eliminated?: Player[];
  former?: Player[];
  outcomeHeading?: string;
  presentation: PlayerCardPresentation;
  extraAction?: HeaderExtra;
  listAction?: ListAction;
  footerAction?: string;
  finished?: boolean;
}

const screens: Record<string, ScreenConfig> = {
  "pending-member": {
    title: "Players",
    players: [johnDoeNoPreferences, wilhelmina, janeDoe, theChancellor],
    presentation: "identity",
    extraAction: "add",
    listAction: { label: "Add player", icon: Send },
  },
  "pending-member-gm": {
    title: "Players",
    gameMaster: zaraGameMaster,
    players: [
      seated(johnDoeNoPreferences),
      wilhelmina,
      janeDoe,
      theChancellor,
    ],
    presentation: "identity",
    extraAction: "add",
    listAction: { label: "Add player", icon: Send },
  },
  "pending-non-member": {
    title: "Players",
    players: [
      { ...johnDoeNoPreferences, isCurrentUser: false },
      wilhelmina,
      janeDoe,
      theChancellor,
    ],
    presentation: "identity",
    extraAction: "join",
    listAction: { label: "Join game", icon: UserPlus },
  },
  mustering: {
    title: "Players",
    players: [johnDoeMustering, janeDoeMustering, theChancellorMustering],
    presentation: "identity",
    extraAction: "confirm",
    footerAction: "Confirm participation",
  },
  "mustering-gm": {
    title: "Players",
    gameMaster: zaraGameMaster,
    players: [
      seated(johnDoeMustering),
      janeDoeMustering,
      theChancellorMustering,
    ],
    presentation: "identity",
    extraAction: "confirm",
    footerAction: "Confirm participation",
  },
  active: {
    title: "Players",
    players: [johnDoeActive, janeDoeActive, theChancellorActive],
    former: [wilhelminaFormer],
    presentation: "nation",
  },
  "active-gm": {
    title: "Players",
    gameMaster: zaraGameMaster,
    players: [seated(johnDoeActive), janeDoeActive, theChancellorActive],
    former: [wilhelminaFormer],
    presentation: "nation",
  },
  "active-eliminated": {
    title: "Players",
    players: [johnDoeActive, janeDoeActive],
    eliminated: [theChancellorEliminated],
    presentation: "nation",
  },
  "active-anon": {
    title: "Players",
    players: [johnDoeAnon, janeDoeAnon],
    presentation: "nation",
  },
  "solo-victory": {
    title: "Results",
    outcomeHeading: "Solo Victory",
    players: [johnDoeSolo],
    eliminated: [janeDoeEliminated, theChancellorEliminated, wilhelminaEliminated],
    presentation: "nation",
    finished: true,
  },
  "solo-victory-gm": {
    title: "Results",
    gameMaster: zaraGameMaster,
    outcomeHeading: "Solo Victory",
    players: [seated(johnDoeSolo)],
    eliminated: [janeDoeEliminated, theChancellorEliminated, wilhelminaEliminated],
    presentation: "nation",
    finished: true,
  },
  draw: {
    title: "Results",
    outcomeHeading: "Draw",
    players: [johnDoeDraw, janeDoeDraw],
    eliminated: [theChancellorEliminated, wilhelminaEliminated],
    presentation: "nation",
    finished: true,
  },
};

const extraButtons: Record<
  HeaderExtra,
  { label: string; icon: LucideIcon }
> = {
  add: { label: "Add player", icon: Send },
  join: { label: "Join game", icon: UserPlus },
  confirm: { label: "Confirm participation", icon: Check },
};

const HeaderButton: React.FC<{
  label: string;
  icon: LucideIcon;
  size: "icon" | "icon-sm";
  withTooltip: boolean;
}> = ({ label, icon: Icon, size, withTooltip }) => {
  const button = (
    <Button size={size} variant="outline" aria-label={label}>
      <Icon />
    </Button>
  );

  if (!withTooltip) {
    return button;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
};

const HeaderActions: React.FC<{
  extraAction?: HeaderExtra;
  size: "icon" | "icon-sm";
  withTooltips: boolean;
}> = ({ extraAction, size, withTooltips }) => {
  const extra = extraAction ? extraButtons[extraAction] : undefined;

  return (
    <div className="flex h-9 items-center gap-1">
      <HeaderButton
        label="Share"
        icon={Share2}
        size={size}
        withTooltip={withTooltips}
      />
      {extra && (
        <HeaderButton
          label={extra.label}
          icon={extra.icon}
          size={size}
          withTooltip={withTooltips}
        />
      )}
    </div>
  );
};

const PlayerSection: React.FC<{
  heading?: string;
  players: Player[];
  presentation: PlayerCardPresentation;
  to?: string;
}> = ({ heading, players, presentation, to = memberPath }) => {
  return (
    <section className="flex flex-col gap-2">
      {heading && (
        <h2 className="text-sm font-medium text-muted-foreground">{heading}</h2>
      )}
      {players.map(player => (
        <PlayerCard
          key={player.id}
          player={player}
          presentation={presentation}
          to={to}
        />
      ))}
    </section>
  );
};

const FormerPlayerSection: React.FC<{
  players: Player[];
  presentation: PlayerCardPresentation;
}> = ({ players, presentation }) => {
  const [open, setOpen] = useState(false);

  if (players.length === 0) {
    return null;
  }

  return (
    <section className="flex flex-col gap-2">
      <button
        type="button"
        className="flex min-h-12 w-full items-center gap-1 text-left text-sm font-medium text-muted-foreground"
        aria-expanded={open}
        onClick={() => setOpen(current => !current)}
      >
        <ChevronDown
          className={cn("size-4 transition-transform", !open && "-rotate-90")}
        />
        Former players ({players.length})
      </button>
      {open && (
        <PlayerSection players={players} presentation={presentation} />
      )}
    </section>
  );
};

const PlayersList: React.FC<{ state: string }> = ({ state }) => {
  const screen = screens[state] ?? screens["pending-member"];
  const eliminated = screen.eliminated ?? [];
  const former = screen.former ?? [];

  return (
    <GameDetailShell
      title={screen.title}
      activeNavItem="Players"
      finished={screen.finished}
      headerAction={
        <HeaderActions
          extraAction={screen.extraAction}
          size="icon-sm"
          withTooltips={false}
        />
      }
    >
      <ScreenContainer>
        <div className="hidden h-9 items-center justify-between gap-2 md:flex">
          <h1 className="min-w-0 truncate text-xl font-semibold leading-9">
            {screen.title}
          </h1>
          <HeaderActions
            extraAction={screen.extraAction}
            size="icon"
            withTooltips
          />
        </div>
        {screen.gameMaster && (
          <PlayerSection
            heading="Game master"
            players={[screen.gameMaster]}
            presentation="identity"
            to={profilePath}
          />
        )}
        <PlayerSection
          heading={
            screen.outcomeHeading ??
            (screen.gameMaster ? "Players" : undefined)
          }
          players={screen.players}
          presentation={screen.presentation}
        />
        {eliminated.length > 0 && (
          <PlayerSection
            heading="Eliminated"
            players={eliminated}
            presentation={screen.presentation}
          />
        )}
        <FormerPlayerSection
          players={former}
          presentation={screen.presentation}
        />
        {screen.listAction && (
          <AddPlayerCard
            label={screen.listAction.label}
            icon={screen.listAction.icon}
            to={memberPath}
          />
        )}
        {screen.footerAction && (
          <Button className="w-full" size="lg">
            <Check />
            {screen.footerAction}
          </Button>
        )}
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { PlayersList };
