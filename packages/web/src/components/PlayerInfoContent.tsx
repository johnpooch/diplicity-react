import React, { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Handshake,
  Link2,
  RotateCcw,
  Star,
  Swords,
  Trophy,
  UserMinus,
  UserPlus,
  UserX,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { AddBotSheet } from "@/components/AddBotSheet";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { NationAssignmentAlert } from "@/components/NationAssignmentAlert";
import {
  NationFlag,
  findNationFlagUrl,
  findNationColor,
  getContrastColor,
} from "@/components/NationFlag";
import { NationSeatFlag, getNationSeatLabel } from "@/components/NationSeat";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
  useGameKickDestroy,
  useUserRetrieveSuspense,
  getGameAddableUserListQueryKey,
  getGameRetrieveQueryKey,
  Member,
  Variant,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { getCurrentPhaseId, isFinishedGameStatus } from "@/util";
import { useRequiredParams } from "@/hooks";
import { copyLink } from "@/utils/copyLink";

const PlayerMedia: React.FC<{
  member: Member;
  variant: Variant | undefined;
  showNationSeat: boolean;
}> = ({ member, variant, showNationSeat }) => {
  if (member.nation && variant && !showNationSeat) {
    const nationColor = findNationColor(variant.nations, member.nation);
    return (
      <div className="relative size-12 shrink-0">
        <div
          className="size-12 overflow-hidden rounded-full"
          style={
            nationColor ? { boxShadow: `0 0 0 3px ${nationColor}` } : undefined
          }
        >
          <NationFlag
            flagUrl={findNationFlagUrl(variant.nations, member.nation)}
            alt={member.nation}
            className="size-12"
            color={nationColor}
          />
        </div>
        {member.userId && (
          <span className="absolute -bottom-0.5 -right-0.5">
            <Avatar className="size-5 ring-2 ring-background">
              <AvatarImage src={member.picture ?? undefined} />
              <AvatarFallback
                className="text-[8px] leading-none"
                style={{
                  backgroundColor: nationColor ?? undefined,
                  color: getContrastColor(nationColor),
                }}
              >
                {member.name[0]?.toUpperCase() ?? "?"}
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
        <AvatarImage src={member.picture ?? undefined} />
        <AvatarFallback>{member.name[0]?.toUpperCase() ?? "?"}</AvatarFallback>
      </Avatar>
      {showNationSeat && variant && (
        <span className="absolute -bottom-0.5 -right-0.5">
          <NationSeatFlag
            nations={variant.nations}
            nation={member.nation}
            preferenceIds={member.nationPreferenceIds}
            size="sm"
          />
        </span>
      )}
    </div>
  );
};

const PlayerMetric: React.FC<{
  label: string;
  icon: React.ReactNode;
  value: number | undefined;
}> = ({ label, icon, value }) => (
  <Tooltip>
    <TooltipTrigger asChild>
      <span
        className="inline-flex items-center gap-1"
        aria-label={value === undefined ? label : `${label}: ${value}`}
        tabIndex={0}
        onPointerDown={event => event.stopPropagation()}
        onClick={event => event.stopPropagation()}
        onKeyDown={event => event.stopPropagation()}
      >
        {icon}
        {value !== undefined ? (
          <span>{value}</span>
        ) : (
          <Skeleton className="h-3 w-4" />
        )}
      </span>
    </TooltipTrigger>
    <TooltipContent side="bottom">{label}</TooltipContent>
  </Tooltip>
);

export const PlayerInfoContent: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { phaseId } = useParams<{ phaseId: string }>();

  const navigate = useNavigate();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const { data: userProfile } = useUserRetrieveSuspense();
  const queryClient = useQueryClient();
  const kickMutation = useGameKickDestroy();

  const [addBotOpen, setAddBotOpen] = useState(false);
  const [formerOpen, setFormerOpen] = useState(true);
  const [memberToRemove, setMemberToRemove] = useState<Member | null>(null);

  const currentPhaseId = getCurrentPhaseId(game);
  const { data: currentPhase } = useGamePhaseRetrieve(
    gameId,
    currentPhaseId ?? 0,
    { query: { enabled: !!currentPhaseId } }
  );

  const getSupplyCenterCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.supplyCenters.filter(
      sc => sc.nation.name === member.nation
    ).length;
  };

  const getUnitCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.units.filter(u => u.nation.name === member.nation)
      .length;
  };

  const isPending = game.status === "pending";
  const isGameMaster =
    !!game.gameMaster && game.gameMaster.userId === userProfile.userId;
  const canTakeOverSeat =
    !game.members.some(m => m.isCurrentUser) && !isGameMaster;
  const playableSeats = variant
    ? variant.nations.filter(n => !n.nonPlayable).length
    : 0;
  const openSeats = isPending
    ? Math.max(0, playableSeats - game.members.length)
    : 0;
  const canAddBots =
    isPending && game.canManage && userProfile.canCreateBotGames;

  const canRemove = (member: Member) =>
    game.canManage &&
    !member.isCurrentUser &&
    member.removable &&
    !(member.eliminated && member.civilDisorder);

  const profilePath = (member: Member) =>
    phaseId
      ? `/game/${gameId}/phase/${phaseId}/player/${member.userId}`
      : `/player/${member.userId}`;

  const handleRemove = async () => {
    const member = memberToRemove;
    setMemberToRemove(null);
    if (!member) return;
    try {
      await kickMutation.mutateAsync({ gameId, memberId: member.id });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGameRetrieveQueryKey(gameId),
        }),
        queryClient.invalidateQueries({
          queryKey: getGameAddableUserListQueryKey(gameId),
        }),
      ]);
      toast.success(`${member.name} removed from the game`);
    } catch {
      toast.error("Failed to remove player");
    }
  };

  const originalOrder = new Map(
    game.members.map((member, index) => [member.id, index])
  );
  const rankMembers = (members: readonly Member[]) =>
    [...members].sort((a, b) => {
      const supplyCenterDifference =
        (getSupplyCenterCount(b) ?? -1) - (getSupplyCenterCount(a) ?? -1);
      if (supplyCenterDifference !== 0) return supplyCenterDifference;

      const unitDifference = (getUnitCount(b) ?? -1) - (getUnitCount(a) ?? -1);
      if (unitDifference !== 0) return unitDifference;

      return (originalOrder.get(a.id) ?? 0) - (originalOrder.get(b.id) ?? 0);
    });

  const isResults = isFinishedGameStatus(game.status);
  const winnerIds = new Set(
    game.victory?.members.map(member => member.id) ?? []
  );
  const winningMembers = isResults
    ? rankMembers(
        game.members.filter(
          member => !member.kicked && winnerIds.has(member.id)
        )
      )
    : [];
  const formerMembers = game.members.filter(member => member.kicked);
  const eliminatedMembers = rankMembers(
    game.members.filter(
      member => member.eliminated && !member.kicked && !winnerIds.has(member.id)
    )
  );
  const activeMembers = rankMembers(
    game.members.filter(
      member =>
        !member.kicked &&
        !member.eliminated &&
        (!isResults || !winnerIds.has(member.id))
    )
  );

  const renderMemberRow = (member: Member, winner = false) => {
    const supplyCenterCount = getSupplyCenterCount(member);
    const unitCount = getUnitCount(member);
    const showNationSeat = isPending && member.isCurrentUser;
    const showRemove = canRemove(member);
    const showActions = member.replaceable || showRemove;
    const isDimmed = member.eliminated || member.civilDisorder;

    const stopRowClick = (e: React.SyntheticEvent) => e.stopPropagation();

    return (
      <div
        key={member.id}
        className={cn("p-3 hover:bg-accent/50", isDimmed && "opacity-70")}
      >
        <div
          className={cn(
            "flex flex-1 min-w-0 items-center gap-3",
            member.userId && "cursor-pointer"
          )}
          role={member.userId ? "link" : undefined}
          tabIndex={member.userId ? 0 : undefined}
          aria-label={
            member.userId ? `View profile for ${member.name}` : undefined
          }
          onClick={
            member.userId ? () => navigate(profilePath(member)) : undefined
          }
          onKeyDown={
            member.userId
              ? e => {
                  if (e.key === "Enter") navigate(profilePath(member));
                }
              : undefined
          }
        >
          <PlayerMedia
            member={member}
            variant={variant}
            showNationSeat={showNationSeat}
          />

          <div className="flex-1 min-w-0">
            {member.nation && !isPending ? (
              <>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium truncate">{member.nation}</span>
                  {member.civilDisorder && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span
                          className="inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-destructive text-white"
                          aria-label="Civil Disorder"
                          tabIndex={0}
                          onPointerDown={event => event.stopPropagation()}
                          onClick={event => event.stopPropagation()}
                          onKeyDown={event => event.stopPropagation()}
                        >
                          <UserX className="size-3" />
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>
                        This player stopped playing and is in Civil Disorder.
                      </TooltipContent>
                    </Tooltip>
                  )}
                  {winner && (
                    <span
                      className="inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-amber-400 text-black"
                      aria-label={
                        game.victory?.type === "solo"
                          ? "Winner"
                          : "Drawn player"
                      }
                    >
                      {game.victory?.type === "solo" ? (
                        <Trophy className="size-3" />
                      ) : (
                        <Handshake className="size-3" />
                      )}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-wrap text-sm mt-0.5 text-muted-foreground">
                  <span>{member.name}</span>
                  {member.isAdmin && <span>(Admin)</span>}
                  {member.isBot && <span>(Bot)</span>}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium">{member.name}</span>
                {member.isAdmin && (
                  <span className="text-sm text-muted-foreground">(Admin)</span>
                )}
                {member.isBot && (
                  <span className="text-sm text-muted-foreground">(Bot)</span>
                )}
                {member.civilDisorder && (
                  <span
                    className="inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-destructive text-white"
                    aria-label="Civil Disorder"
                  >
                    <UserX className="size-3" />
                  </span>
                )}
              </div>
            )}

            {member.isCurrentUser && isPending && (
              <button
                onClick={e => {
                  stopRowClick(e);
                  navigate(`/nation-preference/${gameId}`);
                }}
                onKeyDown={stopRowClick}
                className="flex items-center gap-1 mt-1 text-sm text-muted-foreground hover:text-foreground"
              >
                {getNationSeatLabel(member.nation, member.nationPreferenceIds)}
                <ChevronRight className="size-3.5" />
              </button>
            )}
          </div>

          {member.nation && !isPending && (
            <div className="flex shrink-0 items-center gap-2.5 text-sm text-muted-foreground">
              <PlayerMetric
                label="Supply centres"
                icon={<Star className="size-3" />}
                value={supplyCenterCount}
              />
              <PlayerMetric
                label="Units"
                icon={<Swords className="size-3" />}
                value={unitCount}
              />
              {game.nmrExtensionsAllowed > 0 && (
                <PlayerMetric
                  label="Deadline extensions"
                  icon={<RotateCcw className="size-3" />}
                  value={member.nmrExtensionsRemaining}
                />
              )}
            </div>
          )}

          {member.userId && (
            <ChevronRight className="size-3 shrink-0 text-muted-foreground" />
          )}
        </div>

        {showActions && (
          <div className="flex flex-wrap gap-2 pt-3">
            {member.replaceable && canTakeOverSeat && (
              <Button
                size="sm"
                onClick={() => navigate(`/game/${gameId}/replace/${member.id}`)}
              >
                <UserPlus />
                Replace
              </Button>
            )}
            {member.replaceable && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyLink(`/game/${gameId}/replace/${member.id}`)}
              >
                <Link2 />
                Invite replacement
              </Button>
            )}
            {showRemove && (
              <Button
                variant="outline"
                size="sm"
                aria-label={`Remove ${member.name}`}
                onClick={() => setMemberToRemove(member)}
              >
                <UserMinus />
                Remove player
              </Button>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {!game.victory && (
        <GameStatusAlerts
          game={game}
          variant={variant}
          showPausedNotice={false}
        />
      )}
      {isGameMaster && isPending && <NationAssignmentAlert gameId={gameId} />}

      {game.gameMaster && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            Game master
          </h2>
          <Card className="overflow-hidden py-0">
            <CardContent className="flex items-center gap-3 p-3">
              <Avatar className="size-12">
                <AvatarImage src={game.gameMaster.picture ?? undefined} />
                <AvatarFallback>
                  {game.gameMaster.name[0]?.toUpperCase() ?? "?"}
                </AvatarFallback>
              </Avatar>
              <div className="flex items-center gap-2 flex-wrap flex-1 min-w-0">
                <Link
                  to={`/player/${game.gameMaster.userId}`}
                  className="font-medium text-primary underline-offset-4 hover:underline truncate"
                >
                  {game.gameMaster.name}
                </Link>
                <span className="text-sm text-muted-foreground">(Admin)</span>
              </div>
            </CardContent>
          </Card>
        </section>
      )}

      {winningMembers.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            {game.victory?.type === "solo" ? "Winner" : "Drawn"}
          </h2>
          <Card className="overflow-hidden py-0">
            <CardContent className="flex flex-col divide-y p-0">
              {winningMembers.map(member => renderMemberRow(member, true))}
            </CardContent>
          </Card>
        </section>
      )}

      {(activeMembers.length > 0 || openSeats > 0) && (
        <section className="flex flex-col gap-2">
          {(game.gameMaster || isResults) && (
            <h2 className="text-sm font-medium text-muted-foreground">
              {isResults ? "Other players" : "Players"}
            </h2>
          )}
          <Card className="overflow-hidden py-0">
            <CardContent className="flex flex-col divide-y p-0">
              {activeMembers.map(member => renderMemberRow(member))}
              {Array.from({ length: openSeats }, (_, index) =>
                canAddBots ? (
                  <button
                    key={`open-seat-${index}`}
                    onClick={() => setAddBotOpen(true)}
                    className="flex items-center gap-3 p-3 text-left"
                  >
                    <div className="flex size-12 shrink-0 items-center justify-center rounded-full border border-dashed border-muted-foreground/50">
                      <UserPlus className="size-4 text-muted-foreground" />
                    </div>
                    <span className="font-medium text-primary underline-offset-4 hover:underline">
                      Add AI player
                    </span>
                  </button>
                ) : (
                  <div
                    key={`open-seat-${index}`}
                    className="flex items-center gap-3 p-3"
                  >
                    <div className="size-12 shrink-0 rounded-full border border-dashed border-muted-foreground/50" />
                    <span className="text-muted-foreground">Open seat</span>
                  </div>
                )
              )}
            </CardContent>
          </Card>
        </section>
      )}

      {eliminatedMembers.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            Eliminated
          </h2>
          <Card className="overflow-hidden py-0">
            <CardContent className="flex flex-col divide-y p-0">
              {eliminatedMembers.map(member => renderMemberRow(member))}
            </CardContent>
          </Card>
        </section>
      )}

      {formerMembers.length > 0 && (
        <section className="flex flex-col gap-2">
          <button
            type="button"
            className="flex items-center gap-1 text-sm font-medium text-muted-foreground"
            aria-expanded={formerOpen}
            onClick={() => setFormerOpen(open => !open)}
          >
            <ChevronDown
              className={cn(
                "size-4 transition-transform",
                !formerOpen && "-rotate-90"
              )}
            />
            Former players ({formerMembers.length})
          </button>
          {formerOpen && (
            <Card className="overflow-hidden py-0">
              <CardContent className="flex flex-col divide-y p-0">
                {formerMembers.map(member => renderMemberRow(member))}
              </CardContent>
            </Card>
          )}
        </section>
      )}

      <AlertDialog
        open={memberToRemove !== null}
        onOpenChange={open => !open && setMemberToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Remove {memberToRemove?.nation ?? memberToRemove?.name}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {isPending
                ? `${memberToRemove?.name} is removed from the lobby. They can join again while the game has an open seat.`
                : "Their orders for this phase are discarded and the seat opens for a replacement. They can view the game but cannot rejoin."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemove}>Remove</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {canAddBots && (
        <AddBotSheet
          gameId={gameId}
          open={addBotOpen && openSeats > 0}
          onOpenChange={setAddBotOpen}
        />
      )}
    </>
  );
};
