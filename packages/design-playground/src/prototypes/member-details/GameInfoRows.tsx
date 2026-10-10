import { Link } from "react-router-dom";
import {
  ChevronRight,
  Info,
  RotateCcw,
  Share2,
  Star,
  Swords,
  UserMinus,
  UserPlus,
} from "lucide-react";
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
import { PlayerCard } from "@/components/PlayerCard";
import { memberDetailsStates } from "@/data/fixtures";
import type { MemberDetails } from "@/data/types";

const assignmentPath = "/nation-assignment/single-member/assigned";

const InfoButton: React.FC<{ label: string; text: string }> = ({
  label,
  text,
}) => (
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

const DetailRow: React.FC<{
  label: string;
  value: React.ReactNode;
  info?: string;
  href?: string;
}> = ({ label, value, info, href }) => {
  const body = (
    <>
      <span className="flex min-w-0 items-center gap-1 text-sm">
        {label}
        {info && <InfoButton label={label} text={info} />}
      </span>
      <span className="flex min-w-0 items-center gap-1 text-sm text-muted-foreground">
        <span className="truncate">{value}</span>
        {href && <ChevronRight className="size-4 shrink-0" />}
      </span>
    </>
  );

  if (href) {
    return (
      <Link
        to={href}
        className="flex items-center justify-between gap-4 px-6 py-3 transition-colors hover:bg-accent/50"
      >
        {body}
      </Link>
    );
  }

  return (
    <div className="flex items-center justify-between gap-4 px-6 py-3">
      {body}
    </div>
  );
};

const DetailsCard: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Card className="overflow-hidden py-0">
    <CardContent className="flex flex-col divide-y p-0">{children}</CardContent>
  </Card>
);

const deadlineValue = (member: MemberDetails) =>
  member.deadlineExtensionsAllowed === 0
    ? "Not used in this game"
    : `${member.deadlineExtensionsRemaining} of ${member.deadlineExtensionsAllowed} remaining`;

const RemoveButton: React.FC<{
  control: NonNullable<MemberDetails["removeControl"]>;
}> = ({ control }) => {
  const button = (
    <Button
      variant="outline"
      className="w-full"
      size="lg"
      disabled={!control.enabled}
    >
      <UserMinus />
      Remove from game
    </Button>
  );

  if (control.enabled || !control.reason) return button;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="block">{button}</span>
      </TooltipTrigger>
      <TooltipContent className="max-w-72">{control.reason}</TooltipContent>
    </Tooltip>
  );
};

const GameInfoRows: React.FC<{ state: string }> = ({ state }) => {
  const member =
    memberDetailsStates[state] ?? memberDetailsStates["self-active"];
  const hasCounts =
    member.supplyCenterCount !== undefined || member.unitCount !== undefined;
  const player = {
    ...member.player,
    supplyCenterCount: member.supplyCenterCount,
    unitCount: member.unitCount,
  };

  return (
    <GameDetailShell
      title="Player details"
      activeNavItem="Players"
      mode="secondary"
      backTo="/players-list/game-focused/active"
      finished={member.gameStatus === "completed"}
      headerAction={
        member.canInviteReplacement ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon-sm"
                aria-label="Share replacement link"
              >
                <Share2 />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Share replacement link</TooltipContent>
          </Tooltip>
        ) : undefined
      }
    >
      <ScreenContainer>
        <PlayerCard
          player={player}
          presentation={member.player.anonymous ? "nation" : "identity"}
          to={member.profilePath}
          trailing={
            hasCounts ? (
              <span className="flex items-center gap-3 text-sm text-muted-foreground">
                {member.supplyCenterCount !== undefined && (
                  <span className="flex items-center gap-1">
                    <Star className="size-3.5" />
                    {member.supplyCenterCount}
                  </span>
                )}
                {member.unitCount !== undefined && (
                  <span className="flex items-center gap-1">
                    <Swords className="size-3.5" />
                    {member.unitCount}
                  </span>
                )}
              </span>
            ) : undefined
          }
        />

        {member.canTakeOver && (
          <Button className="w-full" size="lg">
            <UserPlus />
            Take over {member.nation}
          </Button>
        )}

        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            In this game
          </h2>
          <DetailsCard>
            <DetailRow
              label="Nation"
              value={member.nation ?? "Unassigned"}
              href={member.canAssignNation ? assignmentPath : undefined}
            />
            <DetailRow
              label="Participation status"
              value={member.participationStatus}
            />
            <DetailRow
              label="Deadline extensions"
              value={deadlineValue(member)}
              info="If a player does not submit orders on time, a deadline extension is used."
            />
          </DetailsCard>
        </section>

        {member.nationPreferences && (
          <section className="flex flex-col gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">
              Your settings
            </h2>
            <DetailsCard>
              <DetailRow
                label="Nation preferences"
                value={member.nationPreferences.join(" · ")}
                href="/member-details/game-info-rows/self-pending"
              />
            </DetailsCard>
          </section>
        )}

        {(member.canRequestReplacement ||
          member.canCancelReplacement ||
          member.canRecover ||
          member.canInviteReplacement) && (
          <div className="grid gap-2">
            {member.canRecover && (
              <Button variant="outline" className="w-full" size="lg">
                <RotateCcw />
                Return to game
              </Button>
            )}
            {member.canInviteReplacement && (
              <Button variant="outline" className="w-full" size="lg">
                <Share2 />
                Share replacement link
              </Button>
            )}
            {member.canRequestReplacement && (
              <Button variant="outline" className="w-full" size="lg">
                <UserPlus />
                Request replacement
              </Button>
            )}
            {member.canCancelReplacement && (
              <Button variant="outline" className="w-full" size="lg">
                Cancel replacement request
              </Button>
            )}
          </div>
        )}

        {member.canLeave && (
          <Button variant="outline" className="w-full" size="lg">
            Leave game
          </Button>
        )}

        {member.removeControl && (
          <RemoveButton control={member.removeControl} />
        )}
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { GameInfoRows };
