import React, { Suspense } from "react";
import { Link, useNavigate } from "react-router";
import { ChevronRight, Flag, Star, Swords } from "lucide-react";
import { GameDetailAppBar } from "./AppBar";
import { ActionList } from "@/components/ActionList";
import { NationFlag, findNationFlagUrl } from "@/components/NationFlag";
import { Panel } from "@/components/Panel";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { SettingsTable, type SettingsRow } from "@/components/SettingsTable";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useGameMemberRetrieveSuspense,
  useGameRetrieveSuspense,
  MemberDetail,
  ParticipationStatusEnum,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useRequiredParams } from "@/hooks";

const PARTICIPATION_LABELS: Record<ParticipationStatusEnum, string> = {
  game_master: "Game master",
  replaced: "Replaced",
  removed: "Removed",
  withdrawn: "Withdrawn",
  won: "Won",
  drew: "Drew",
  eliminated: "Eliminated",
  civil_disorder: "Civil disorder",
  seat_unconfirmed: "Seat not confirmed",
  seat_confirmed: "Seat confirmed",
  joined: "Joined",
  playing: "Playing",
};

const roleLabel = (member: MemberDetail) => {
  if (member.participationStatus === "game_master") return "Game master";
  if (member.isAdmin) return "Admin";
  if (member.isBot) return "Bot";
  return null;
};

interface PlayerCardProps {
  member: MemberDetail;
  profilePath: string;
}

const PlayerCard: React.FC<PlayerCardProps> = ({ member, profilePath }) => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const role = roleLabel(member);
  const subtitle = [member.nation ? member.name : null, role]
    .filter(Boolean)
    .join(" · ");

  const content = (
    <CardContent className="flex items-center gap-3 p-3">
      <div className="relative">
        <Avatar className="size-12">
          <AvatarImage src={member.picture ?? undefined} />
          <AvatarFallback>{member.name[0]?.toUpperCase() ?? "?"}</AvatarFallback>
        </Avatar>
        {member.nation && variant && (
          <NationFlag
            flagUrl={findNationFlagUrl(variant.nations, member.nation)}
            alt={member.nation}
            className="absolute -bottom-0.5 -right-0.5 size-5 rounded-full ring-2 ring-background"
          />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{member.nation ?? member.name}</p>
        {subtitle && (
          <p className="text-sm text-muted-foreground truncate">{subtitle}</p>
        )}
      </div>
      {member.supplyCenterCount !== null && member.unitCount !== null && (
        <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1" aria-label={`Supply centres: ${member.supplyCenterCount}`}>
            <Star className="size-3" />
            {member.supplyCenterCount}
          </span>
          <span className="inline-flex items-center gap-1" aria-label={`Units: ${member.unitCount}`}>
            <Swords className="size-3" />
            {member.unitCount}
          </span>
        </div>
      )}
      {member.userId !== null && (
        <ChevronRight className="size-4 text-muted-foreground" />
      )}
    </CardContent>
  );

  return (
    <Card className="overflow-hidden py-0">
      {member.userId !== null ? (
        <Link
          to={profilePath}
          aria-label={`View profile for ${member.name}`}
          className="hover:bg-accent/50"
        >
          {content}
        </Link>
      ) : (
        content
      )}
    </Card>
  );
};

const MemberContent: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId, memberId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    memberId: string;
  }>();
  const { data: member } = useGameMemberRetrieveSuspense(
    gameId,
    Number(memberId)
  );
  const isGameMaster = member.participationStatus === "game_master";

  const gameRows: SettingsRow[] = [
    ...(isGameMaster
      ? []
      : [{ key: "nation", label: "Nation", value: member.nation ?? "Unassigned" }]),
    {
      key: "status",
      label: "Participation status",
      value: PARTICIPATION_LABELS[member.participationStatus],
    },
    ...(isGameMaster || member.nmrExtensionsAllowed === 0
      ? []
      : [
          {
            key: "extensions",
            label: "Deadline extensions",
            value: `${member.nmrExtensionsRemaining} of ${member.nmrExtensionsAllowed} remaining`,
          },
        ]),
  ];

  return (
    <div className="flex flex-col gap-4">
      <ActionList
        gameId={gameId}
        actions={member.actions}
        member={member}
        onMemberGone={() =>
          navigate(`/game/${gameId}/phase/${phaseId}/player-info`)
        }
      >
        <PlayerCard
          member={member}
          profilePath={`/game/${gameId}/phase/${phaseId}/player/${member.userId}?member=${member.id}`}
        />
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">In this game</h2>
          <SettingsTable rows={gameRows} />
        </section>
        {member.nationPreferences !== null && (
          <section className="flex flex-col gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">Your settings</h2>
            <Card className="overflow-hidden py-0">
              <Link
                to={`/game/${gameId}/phase/${phaseId}/nation-preference`}
                className="flex items-center justify-between gap-4 px-6 py-3 text-sm hover:bg-accent/50"
              >
                <span>Nation preferences</span>
                <span className="flex min-w-0 items-center gap-1 text-muted-foreground">
                  <span className="truncate">
                    {member.nationPreferences.length > 0
                      ? member.nationPreferences.join(", ")
                      : "Not set"}
                  </span>
                  <ChevronRight className="size-4 shrink-0" />
                </span>
              </Link>
            </Card>
          </section>
        )}
      </ActionList>
      {member.canReport && (
        <Button variant="secondary" asChild>
          <Link to={`/game/${gameId}/phase/${phaseId}/member/${member.id}/report`}>
            <Flag />
            Report player
          </Link>
        </Button>
      )}
      {member.alreadyReported && (
        <Button variant="secondary" disabled>
          <Flag />
          Report player
        </Button>
      )}
    </div>
  );
};

const MemberContentSkeleton: React.FC = () => (
  <div className="flex flex-col gap-4">
    <Skeleton className="h-[74px] w-full rounded-xl" />
    <div className="flex flex-col gap-2">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-[136px] w-full rounded-xl" />
    </div>
    <Skeleton className="h-9 w-full" />
  </div>
);

const MemberScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Player details"
        onNavigateBack={() =>
          navigate(`/game/${gameId}/phase/${phaseId}/player-info`)
        }
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="px-3 py-4 md:p-2">
            <QueryErrorBoundary>
              <Suspense fallback={<MemberContentSkeleton />}>
                <MemberContent />
              </Suspense>
            </QueryErrorBoundary>
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

export { MemberScreen };
