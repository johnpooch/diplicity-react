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
import { ListItem, ListSection } from "@/components/ui/list";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import { PlayerCard } from "@/components/PlayerCard";
import { memberDetailsStates } from "@/data/fixtures";
import type { MemberDetails } from "@/data/types";

const assignmentPath = "/nation-assignment/single-member/assigned";

const roleLabel = (member: MemberDetails) => {
  if (member.player.role === "admin") return "Game admin";
  if (member.player.role === "bot") return "Bot";
  return "Player";
};

const statusVariant = (member: MemberDetails) => {
  if (
    member.participationStatus === "Civil disorder" ||
    member.participationStatus === "Removed" ||
    member.participationStatus === "Eliminated"
  ) {
    return "destructive" as const;
  }
  if (member.participationStatus === "Playing") return "outline" as const;
  return "secondary" as const;
};

const deadlineValue = (member: MemberDetails) =>
  member.deadlineExtensionsAllowed === 0
    ? "Not used in this game"
    : `${member.deadlineExtensionsRemaining} of ${member.deadlineExtensionsAllowed} remaining`;

const ActionCard: React.FC<{
  title: string;
  body: string;
  children: React.ReactNode;
}> = ({ title, body, children }) => (
  <Card className="py-0">
    <CardContent className="flex flex-col gap-3 p-3">
      <div>
        <p className="font-semibold">{title}</p>
        <p className="text-sm text-muted-foreground">{body}</p>
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </CardContent>
  </Card>
);

const GroupedSections: React.FC<{ state: string }> = ({ state }) => {
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

        <ListSection header="In this game">
          <ListItem
            leading={
              member.nation ? (
                <NationFlag nation={member.nation} size="md" />
              ) : null
            }
            title="Nation"
            subtitle={member.nation ?? "Unassigned"}
            href={member.canAssignNation ? assignmentPath : undefined}
            trailing={
              member.canAssignNation ? (
                <ChevronRight className="size-4 text-muted-foreground" />
              ) : undefined
            }
          />
          <ListItem title="Role" trailing={roleLabel(member)} />
          <ListItem
            title="Participation status"
            trailing={
              <Badge variant={statusVariant(member)}>
                {member.participationStatus}
              </Badge>
            }
          />
          {hasPosition && (
            <ListItem
              title="Current position"
              trailing={
                <span className="flex items-center gap-3 text-sm text-muted-foreground">
                  {member.supplyCenterCount !== undefined && (
                    <span className="flex items-center gap-1">
                      <Star className="size-3.5" />
                      {member.supplyCenterCount} centres
                    </span>
                  )}
                  {member.unitCount !== undefined && (
                    <span className="flex items-center gap-1">
                      <Swords className="size-3.5" />
                      {member.unitCount} units
                    </span>
                  )}
                </span>
              }
            />
          )}
          <ListItem
            title="Deadline extensions"
            subtitle="Used automatically after a missed movement deadline"
            trailing={deadlineValue(member)}
          />
          {member.result && (
            <ListItem title="Result" trailing={member.result} />
          )}
        </ListSection>

        {member.nationPreferences && (
          <ListSection header="Your settings">
            <ListItem
              title="Nation preferences"
              subtitle={member.nationPreferences.join(" · ")}
              onClick={() => undefined}
              trailing={
                <ChevronRight className="size-4 text-muted-foreground" />
              }
              ariaLabel="Edit nation preferences"
            />
          </ListSection>
        )}

        {hasReplacementActions && (
          <section className="flex flex-col gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">
              Participation
            </h2>
            <ActionCard
              title={
                member.participationStatus === "Civil disorder"
                  ? "This seat needs a player"
                  : "Replacement"
              }
              body={
                member.canTakeOver
                  ? `Take over ${member.nation ?? "this nation"}, or invite someone else.`
                  : "Manage who will continue playing this nation."
              }
            >
              {member.canRecover && (
                <Button>
                  <RotateCcw />
                  Return to game
                </Button>
              )}
              {member.canTakeOver && (
                <Button>
                  <UserPlus />
                  Take over {member.nation}
                </Button>
              )}
              {member.canInviteReplacement && (
                <Button variant="outline">
                  <ClipboardCopy />
                  Invite replacement
                </Button>
              )}
              {member.canRequestReplacement && (
                <Button variant="outline">
                  <UserPlus />
                  Request replacement
                </Button>
              )}
              {member.canCancelReplacement && (
                <Button variant="outline">Cancel replacement request</Button>
              )}
            </ActionCard>
          </section>
        )}

        {(member.canLeave || member.removeControl) && (
          <section className="flex flex-col gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">
              {member.removeControl ? "Manage player" : "Leave this game"}
            </h2>
            <ActionCard
              title={member.removeControl ? "Remove from game" : "Leave game"}
              body={
                member.removeControl?.reason ??
                "You will give up your place in this game."
              }
            >
              {member.canLeave && (
                <Button variant="destructive">
                  <LogOut />
                  Leave game
                </Button>
              )}
              {member.removeControl && (
                <Button
                  variant="destructive"
                  disabled={!member.removeControl.enabled}
                >
                  {member.removeControl.enabled ? (
                    <UserMinus />
                  ) : (
                    <ShieldAlert />
                  )}
                  Remove from game
                </Button>
              )}
            </ActionCard>
          </section>
        )}

        {member.canAssignNation && (
          <Button variant="link" className="w-full" asChild>
            <Link to={assignmentPath}>Open focused nation assignment</Link>
          </Button>
        )}
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { GroupedSections };
