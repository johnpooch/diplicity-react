import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ListItem, ListSection } from "@/components/ui/list";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlagsProvider } from "@/components/NationFlag";
import { PlayerMedia } from "@/components/PlayerCard";
import { cn } from "@/lib/utils";
import {
  giuseppeActive,
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
  ottoActive,
  sultanActive,
  theChancellor,
  theChancellorActive,
  theChancellorEliminated,
  theChancellorMustering,
  tsarinaActive,
  wilhelmina,
  wilhelminaEliminated,
  wilhelminaFormer,
  zaraGameMaster,
} from "@/data/fixtures";
import type { Player, PlayerCardPresentation } from "@/data/types";
import {
  Check,
  ChevronDown,
  ChevronRight,
  Send,
  Share2,
  Star,
  Swords,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

const memberPath = "/player-card/member-destination";
const profilePath = "/player-profile/stat-grid";

const seated = (player: Player): Player =>
  player.role === "admin" ? { ...player, role: undefined } : player;

const activeBoard: Player[] = [
  johnDoeActive,
  janeDoeActive,
  theChancellorActive,
  ottoActive,
  giuseppeActive,
  tsarinaActive,
  sultanActive,
];

const rankByStrength = (players: Player[]) =>
  [...players].sort((a, b) => {
    const centres =
      (b.supplyCenterCount ?? 0) - (a.supplyCenterCount ?? 0);
    if (centres !== 0) return centres;
    return (a.assignedNation ?? a.name).localeCompare(
      b.assignedNation ?? b.name,
    );
  });

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
  hideFlags?: boolean;
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
    players: activeBoard,
    former: [wilhelminaFormer],
    presentation: "nation",
  },
  "active-no-flags": {
    title: "Players",
    players: activeBoard,
    former: [wilhelminaFormer],
    presentation: "nation",
    hideFlags: true,
  },
  "active-gm": {
    title: "Players",
    gameMaster: zaraGameMaster,
    players: [seated(johnDoeActive), ...activeBoard.slice(1)],
    former: [wilhelminaFormer],
    presentation: "nation",
  },
  "active-eliminated": {
    title: "Players",
    players: activeBoard.filter(player => player.id !== "the-chancellor"),
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

const displayName = (player: Player) =>
  player.anonymous ? "Anonymous" : player.name;

const roleLabel = (player: Player) => {
  if (player.role === "admin") return "admin";
  if (player.role === "bot") return "bot";
  return undefined;
};

const playerSubtitle = (player: Player, presentation: PlayerCardPresentation) => {
  const name = displayName(player);
  const role = roleLabel(player);
  const named = role ? `${name} (${role})` : name;

  if (presentation === "nation" && player.assignedNation) {
    return named;
  }

  return player.status;
};

const playerTitle = (player: Player, presentation: PlayerCardPresentation) => {
  if (presentation === "nation" && player.assignedNation) {
    return player.assignedNation;
  }

  const name = displayName(player);
  const role = roleLabel(player);
  if (!role) return name;

  return (
    <>
      {name}
      <span className="font-normal text-muted-foreground"> ({role})</span>
    </>
  );
};

const PlayerStats: React.FC<{ player: Player }> = ({ player }) => {
  if (
    player.supplyCenterCount === undefined &&
    player.unitCount === undefined
  ) {
    return null;
  }

  return (
    <span className="flex shrink-0 items-center gap-2.5 text-sm text-muted-foreground">
      {player.supplyCenterCount !== undefined && (
        <span className="flex items-center gap-1">
          <Star className="size-3.5" />
          {player.supplyCenterCount}
        </span>
      )}
      {player.unitCount !== undefined && (
        <span className="flex items-center gap-1">
          <Swords className="size-3.5" />
          {player.unitCount}
        </span>
      )}
    </span>
  );
};

const PlayerRow: React.FC<{
  player: Player;
  presentation: PlayerCardPresentation;
  to: string;
  dimmed?: boolean;
}> = ({ player, presentation, to, dimmed = false }) => {
  const showStats =
    presentation === "nation" && Boolean(player.assignedNation);

  return (
    <ListItem
      href={to}
      className={dimmed ? "opacity-70" : undefined}
      leading={<PlayerMedia player={player} presentation={presentation} />}
      title={playerTitle(player, presentation)}
      subtitle={playerSubtitle(player, presentation)}
      trailing={
        <span className="flex items-center gap-2">
          {showStats && <PlayerStats player={player} />}
          <ChevronRight className="size-4 text-muted-foreground" />
        </span>
      }
    />
  );
};

const PlayerSection: React.FC<{
  heading?: string;
  players: Player[];
  presentation: PlayerCardPresentation;
  to?: string;
  dimmed?: boolean;
}> = ({ heading, players, presentation, to = memberPath, dimmed = false }) => {
  return (
    <ListSection header={heading}>
      {players.map(player => (
        <PlayerRow
          key={player.id}
          player={player}
          presentation={presentation}
          to={to}
          dimmed={dimmed}
        />
      ))}
    </ListSection>
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
  const nationFirst = screen.presentation === "nation";
  const players = nationFirst
    ? rankByStrength(screen.players)
    : screen.players;
  const eliminated = nationFirst
    ? rankByStrength(screen.eliminated ?? [])
    : (screen.eliminated ?? []);
  const former = screen.former ?? [];
  const ListActionIcon = screen.listAction?.icon;

  return (
    <NationFlagsProvider enabled={!screen.hideFlags}>
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
          players={players}
          presentation={screen.presentation}
        />
        {eliminated.length > 0 && (
          <PlayerSection
            heading="Eliminated"
            players={eliminated}
            presentation={screen.presentation}
            dimmed
          />
        )}
        <FormerPlayerSection
          players={former}
          presentation={screen.presentation}
        />
        {screen.listAction && ListActionIcon && (
          <Button className="w-full" size="lg" asChild>
            <Link to={memberPath}>
              <ListActionIcon />
              {screen.listAction.label}
            </Link>
          </Button>
        )}
        {screen.footerAction && (
          <Button className="w-full" size="lg">
            {screen.footerAction}
          </Button>
        )}
      </ScreenContainer>
    </GameDetailShell>
    </NationFlagsProvider>
  );
};

export { PlayersList };
