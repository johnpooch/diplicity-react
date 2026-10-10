import { Link } from "react-router-dom";
import {
  ChevronRight,
  ClipboardCopy,
  LogOut,
  RotateCcw,
  ShieldAlert,
  Star,
  Swords,
  UserMinus,
  UserPlus,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import { PlayerCard } from "@/components/PlayerCard";
import { memberDetailsStates } from "@/data/fixtures";
import type { MemberDetails } from "@/data/types";

const assignmentPath = "/nation-assignment/single-member/assigned";

const statusClassName = (status: MemberDetails["participationStatus"]) => {
  if (
    status === "Civil disorder" ||
    status === "Removed" ||
    status === "Eliminated"
  ) {
    return "border-destructive/20 bg-destructive/10 text-destructive";
  }
  return "border-border bg-muted text-foreground";
};

const Metric: React.FC<{
  value: React.ReactNode;
  label: string;
  icon?: React.ReactNode;
}> = ({ value, label, icon }) => (
  <div className="flex min-w-0 flex-col items-center gap-1 px-2 text-center">
    <div className="flex items-center gap-1 text-xl font-semibold tabular-nums">
      {icon}
      {value}
    </div>
    <p className="text-xs leading-tight text-muted-foreground">{label}</p>
  </div>
);

const SnapshotPanel: React.FC<{ state: string }> = ({ state }) => {
  const member =
    memberDetailsStates[state] ?? memberDetailsStates["self-active"];
  const hasPosition =
    member.supplyCenterCount !== undefined || member.unitCount !== undefined;
  const hasReplacementActions =
    member.canRequestReplacement ||
    member.canCancelReplacement ||
    member.canRecover ||
    member.canInviteReplacement ||
    member.canTakeOver;

  return (
    <GameDetailShell
      title="Player details"
      activeNavItem="Players"
      mode="secondary"
      backTo="/players-list/game-focused/active"
      finished={member.gameStatus === "completed"}
    >
      <ScreenContainer>
        <PlayerCard
          player={member.player}
          presentation={member.player.anonymous ? "nation" : "identity"}
          to={member.profilePath}
        />

        <Card className="overflow-hidden py-0">
          <CardContent className="p-0">
            <div className="flex items-center gap-3 border-b p-4">
              {member.nation ? (
                <NationFlag nation={member.nation} size="lg" />
              ) : (
                <div className="flex size-12 items-center justify-center rounded-full border border-dashed text-xs text-muted-foreground">
                  None
                </div>
              )}
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Nation
                </p>
                <p className="truncate text-lg font-semibold">
                  {member.nation ?? "Unassigned"}
                </p>
              </div>
              {member.canAssignNation && (
                <Button variant="outline" size="sm" asChild>
                  <Link to={assignmentPath}>
                    Edit
                    <ChevronRight />
                  </Link>
                </Button>
              )}
            </div>

            <div
              className={`grid ${hasPosition ? "grid-cols-3" : "grid-cols-1"} divide-x py-4`}
            >
              {member.supplyCenterCount !== undefined && (
                <Metric
                  value={member.supplyCenterCount}
                  label="Supply centres"
                  icon={<Star className="size-4 text-muted-foreground" />}
                />
              )}
              {member.unitCount !== undefined && (
                <Metric
                  value={member.unitCount}
                  label="Units"
                  icon={<Swords className="size-4 text-muted-foreground" />}
                />
              )}
              <Metric
                value={
                  member.deadlineExtensionsAllowed === 0
                    ? "—"
                    : `${member.deadlineExtensionsRemaining}/${member.deadlineExtensionsAllowed}`
                }
                label="Deadline extensions remaining"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2 border-t px-4 py-3">
              <Badge
                variant="outline"
                className={statusClassName(member.participationStatus)}
              >
                {member.participationStatus}
              </Badge>
              <Badge variant="outline">
                {member.player.role === "admin"
                  ? "Game admin"
                  : member.player.role === "bot"
                    ? "Bot"
                    : "Player"}
              </Badge>
              {member.result && (
                <Badge variant="secondary">{member.result}</Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {member.nationPreferences && (
          <button
            type="button"
            className="flex w-full items-center gap-3 rounded-xl border bg-card p-4 text-left transition-colors hover:bg-accent/50"
          >
            <div className="min-w-0 flex-1">
              <p className="font-semibold">Nation preferences</p>
              <p className="truncate text-sm text-muted-foreground">
                {member.nationPreferences.join(" · ")}
              </p>
            </div>
            <ChevronRight className="size-4 text-muted-foreground" />
          </button>
        )}

        {hasReplacementActions && (
          <Card className="py-0">
            <CardContent className="flex flex-col gap-3 p-4">
              <div>
                <p className="font-semibold">
                  {member.participationStatus === "Civil disorder"
                    ? "This seat needs a player"
                    : "Continue this nation"}
                </p>
                <p className="text-sm text-muted-foreground">
                  {member.canTakeOver
                    ? `You can take over ${member.nation}, or share the invitation.`
                    : "Choose what should happen to this place in the game."}
                </p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {member.canRecover && (
                  <Button className="w-full">
                    <RotateCcw />
                    Return to game
                  </Button>
                )}
                {member.canTakeOver && (
                  <Button className="w-full">
                    <UserPlus />
                    Take over {member.nation}
                  </Button>
                )}
                {member.canInviteReplacement && (
                  <Button variant="outline" className="w-full">
                    <ClipboardCopy />
                    Invite replacement
                  </Button>
                )}
                {member.canRequestReplacement && (
                  <Button variant="outline" className="w-full">
                    <UserPlus />
                    Request replacement
                  </Button>
                )}
                {member.canCancelReplacement && (
                  <Button variant="outline" className="w-full sm:col-span-2">
                    Cancel replacement request
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {(member.canLeave || member.removeControl) && (
          <div className="rounded-xl border border-destructive/25 bg-destructive/5 p-4">
            <div className="mb-3">
              <p className="font-semibold text-destructive">
                {member.removeControl ? "Manage player" : "Leave this game"}
              </p>
              <p className="text-sm text-muted-foreground">
                {member.removeControl?.reason ??
                  "You will give up your place in this game."}
              </p>
            </div>
            {member.canLeave && (
              <Button variant="destructive" className="w-full">
                <LogOut />
                Leave game
              </Button>
            )}
            {member.removeControl && (
              <Button
                variant="destructive"
                className="w-full"
                disabled={!member.removeControl.enabled}
              >
                {member.removeControl.enabled ? <UserMinus /> : <ShieldAlert />}
                Remove from game
              </Button>
            )}
          </div>
        )}
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { SnapshotPanel };
