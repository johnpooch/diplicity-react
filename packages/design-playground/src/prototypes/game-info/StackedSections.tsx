import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GameDetailShell } from "@/components/GameDetailShell";
import { VariantCard } from "@/components/VariantCard";
import {
  brushOfFrameGunboat,
  brushOfFrameHighCommitment,
  brushOfFramePending,
  brushOfFramePendingNoExtensions,
  brushOfFramePrivate,
  brushOfFramePrivateGunboat,
} from "@/data/fixtures";
import type {
  GameInfo,
  GameInfoSetting,
  GameInfoSettingIcon,
} from "@/data/types";
import {
  Calendar,
  Info,
  Lock,
  MessageCircleOff,
  Share2,
  ShieldPlus,
  UserPlus,
  type LucideIcon,
} from "lucide-react";

const settingIcons: Record<GameInfoSettingIcon, LucideIcon> = {
  calendar: Calendar,
  lock: Lock,
  "shield-plus": ShieldPlus,
  "message-circle-off": MessageCircleOff,
};

const HeaderButton: React.FC<{
  label: string;
  icon: LucideIcon;
  size: "icon" | "icon-sm";
  withTooltip: boolean;
  disabled?: boolean;
}> = ({ label, icon: Icon, size, withTooltip, disabled }) => {
  const button = (
    <Button
      size={size}
      variant="outline"
      aria-label={label}
      disabled={disabled}
    >
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

const InfoButton: React.FC<{ label: string; text: string }> = ({
  label,
  text,
}) => {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="-m-2 p-2 text-muted-foreground/60 hover:text-muted-foreground"
          aria-label={`What are ${label}?`}
        >
          <Info className="size-3.5" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="text-sm">{text}</PopoverContent>
    </Popover>
  );
};

const SettingsTable: React.FC<{ rows: GameInfoSetting[] }> = ({ rows }) => {
  return (
    <Card className="overflow-hidden py-0">
      <CardContent className="flex flex-col divide-y p-0">
        {rows.map(row => {
          const Icon = row.icon ? settingIcons[row.icon] : undefined;

          return (
            <div
              key={row.label}
              className="flex items-center justify-between gap-4 px-6 py-3"
            >
              <span className="flex min-w-0 items-center gap-3 text-sm">
                {Icon && (
                  <Icon className="size-4 shrink-0 text-muted-foreground" />
                )}
                <span className="flex min-w-0 items-center gap-1">
                  {row.label}
                  {row.info && <InfoButton label={row.label} text={row.info} />}
                </span>
              </span>
              {row.value && (
                <span className="truncate text-sm text-muted-foreground">
                  {row.value}
                </span>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
};

const HeaderActions: React.FC<{
  size: "icon" | "icon-sm";
  withTooltips: boolean;
  joinDisabled?: boolean;
  showJoin?: boolean;
}> = ({ size, withTooltips, joinDisabled, showJoin = true }) => {
  return (
    <div className="flex h-9 items-center gap-1">
      <HeaderButton
        label="Share"
        icon={Share2}
        size={size}
        withTooltip={withTooltips}
      />
      {showJoin && (
        <HeaderButton
          label="Join game"
          icon={UserPlus}
          size={size}
          withTooltip={withTooltips}
          disabled={joinDisabled}
        />
      )}
    </div>
  );
};

interface ScreenConfig {
  game: GameInfo;
  showJoin?: boolean;
  footerAction: {
    label: string;
    variant?: "default" | "outline";
    disabled?: boolean;
  };
}

const screens: Record<string, ScreenConfig> = {
  pending: {
    game: brushOfFramePending,
    footerAction: { label: "Join Game" },
  },
  "no-extensions": {
    game: brushOfFramePendingNoExtensions,
    footerAction: { label: "Join Game" },
  },
  private: {
    game: brushOfFramePrivate,
    footerAction: { label: "Join Game" },
  },
  "high-commitment": {
    game: brushOfFrameHighCommitment,
    footerAction: { label: "Join Game", disabled: true },
  },
  gunboat: {
    game: brushOfFrameGunboat,
    footerAction: { label: "Join Game" },
  },
  "private-gunboat": {
    game: brushOfFramePrivateGunboat,
    footerAction: { label: "Join Game" },
  },
  joined: {
    game: brushOfFramePending,
    showJoin: false,
    footerAction: { label: "Leave Game", variant: "outline" },
  },
};

const GameInfo: React.FC<{ state: string }> = ({ state }) => {
  const screen = screens[state] ?? screens.pending;
  const game = screen.game;
  const showJoin = screen.showJoin ?? true;

  return (
    <GameDetailShell
      title={game.name}
      activeNavItem="Info"
      headerAction={
        <HeaderActions
          size="icon-sm"
          withTooltips={false}
          joinDisabled={screen.footerAction.disabled}
          showJoin={showJoin}
        />
      }
    >
      <ScreenContainer>
        <div className="hidden h-9 items-center justify-between gap-2 md:flex">
          <h1 className="min-w-0 truncate text-xl font-semibold leading-9">
            {game.name}
          </h1>
          <HeaderActions
            size="icon"
            withTooltips
            joinDisabled={screen.footerAction.disabled}
            showJoin={showJoin}
          />
        </div>
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">Variant</h2>
          <VariantCard
            compact
            variant={game.variant}
            to={`/variant-detail/full-page/${game.variant.id}`}
          />
        </section>
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            Phase deadlines
          </h2>
          <SettingsTable rows={game.phaseDeadlines} />
        </section>
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            Game settings
          </h2>
          <SettingsTable rows={game.settings} />
        </section>
        <Button
          className="w-full"
          size="lg"
          variant={screen.footerAction.variant}
          disabled={screen.footerAction.disabled}
        >
          {screen.footerAction.label}
        </Button>
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { GameInfo };
