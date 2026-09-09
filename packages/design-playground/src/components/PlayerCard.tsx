import { Link } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { NationFlag } from "@/components/NationFlag";
import { cn } from "@/lib/utils";
import { Plus, Star, Swords, UserPlus, type LucideIcon } from "lucide-react";
import type { Player, PlayerCardPresentation } from "@/data/types";

interface PlayerCardProps {
  player: Player;
  presentation: PlayerCardPresentation;
  to: string;
  className?: string;
}

const displayName = (player: Player) =>
  player.anonymous ? "Anonymous" : player.name;

const roleLabel = (player: Player) => {
  if (player.role === "admin") return "admin";
  if (player.role === "bot") return "bot";
  return undefined;
};

const initials = (player: Player) => displayName(player).charAt(0).toUpperCase();

const FlagOverlay: React.FC<{ nation: string; preferred?: boolean }> = ({
  nation,
  preferred = false,
}) => {
  return (
    <span
      className={cn(
        "absolute -bottom-0.5 -right-0.5 size-5 overflow-hidden rounded-full bg-card",
        preferred
          ? "border border-dashed border-foreground"
          : "ring-2 ring-card"
      )}
    >
      <NationFlag nation={nation} />
    </span>
  );
};

const EmptyNationOverlay: React.FC<{ withPlus?: boolean }> = ({
  withPlus = false,
}) => {
  return (
    <span className="absolute -bottom-0.5 -right-0.5 flex size-5 items-center justify-center rounded-full border border-dashed border-foreground bg-card opacity-70">
      {withPlus && <Plus className="size-3" />}
    </span>
  );
};

const PlayerMedia: React.FC<{
  player: Player;
  presentation: PlayerCardPresentation;
}> = ({ player, presentation }) => {
  if (presentation === "nation" && player.assignedNation) {
    return (
      <div className="relative size-12 shrink-0">
        <div className="size-12 overflow-hidden rounded-full border">
          <NationFlag nation={player.assignedNation} />
        </div>
        {!player.anonymous && (
          <span className="absolute -bottom-0.5 -right-0.5">
            <Avatar className="size-5 ring-2 ring-card">
              {player.picture && <AvatarImage src={player.picture} alt="" />}
              <AvatarFallback className="text-[8px]">
                {initials(player)}
              </AvatarFallback>
            </Avatar>
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="relative size-12 shrink-0">
      <Avatar className="size-12">
        {player.picture && !player.anonymous && (
          <AvatarImage src={player.picture} alt="" />
        )}
        <AvatarFallback>{initials(player)}</AvatarFallback>
      </Avatar>
      {!player.gameMaster &&
        (player.assignedNation ? (
          <FlagOverlay nation={player.assignedNation} />
        ) : player.preferredNation ? (
          <FlagOverlay nation={player.preferredNation} preferred />
        ) : (
          <EmptyNationOverlay withPlus={player.isCurrentUser} />
        ))}
    </div>
  );
};

const NationStats: React.FC<{ player: Player }> = ({ player }) => {
  return (
    <div className="flex min-w-0 items-center justify-between gap-3">
      <p className="truncate font-semibold leading-tight">
        {player.assignedNation}
      </p>
      <p className="flex shrink-0 items-center gap-2.5 text-sm text-muted-foreground">
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
      </p>
    </div>
  );
};

const PlayerCard: React.FC<PlayerCardProps> = ({
  player,
  presentation,
  to,
  className,
}) => {
  const name = displayName(player);
  const role = roleLabel(player);
  const showNationStats =
    presentation === "nation" && Boolean(player.assignedNation);

  return (
    <Link to={to} className={cn("block", className)}>
      <Card className="overflow-hidden py-0 transition-colors hover:bg-accent/50">
        <CardContent className="flex items-center gap-3 p-3">
          <PlayerMedia player={player} presentation={presentation} />
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            {showNationStats ? (
              <>
                <NationStats player={player} />
                <p className="truncate text-sm text-muted-foreground">
                  {name}
                  {role && ` (${role})`}
                </p>
              </>
            ) : (
              <>
                <p className="truncate leading-tight">
                  <span className="font-semibold">{name}</span>
                  {role && (
                    <span className="text-muted-foreground"> ({role})</span>
                  )}
                </p>
                {player.status && (
                  <p className="truncate text-sm text-muted-foreground">
                    {player.status}
                  </p>
                )}
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};

interface AddPlayerCardProps {
  label: string;
  to: string;
  icon?: LucideIcon;
  className?: string;
}

const AddPlayerCard: React.FC<AddPlayerCardProps> = ({
  label,
  to,
  icon: Icon = UserPlus,
  className,
}) => {
  return (
    <Link to={to} className={cn("block", className)}>
      <Card className="overflow-hidden py-0 transition-colors hover:bg-accent/50">
        <CardContent className="flex items-center gap-3 p-3">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-full border border-dashed border-muted-foreground">
            <Icon className="size-5 text-muted-foreground" />
          </div>
          <p className="font-semibold leading-tight">{label}</p>
        </CardContent>
      </Card>
    </Link>
  );
};

export { PlayerCard, AddPlayerCard };
