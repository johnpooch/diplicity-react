import React, { Suspense, useState } from "react";
import { Link, useNavigate } from "react-router";
import { toast } from "sonner";
import { Ban, Check, Clock, Handshake, Undo2, X } from "lucide-react";
import { useRequiredParams } from "@/hooks";
import { useQueryClient } from "@tanstack/react-query";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "../../components/Panel";
import { Notice } from "@/components/Notice";
import {
  useGameRetrieveSuspense,
  useGamesDrawProposalsListSuspense,
  useGamesDrawProposalsVotePartialUpdate,
  useGamesDrawProposalsCancelDestroy,
  getGamesDrawProposalsListQueryKey,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";
import type { DrawProposal } from "@/api/generated/endpoints";
import { getCurrentPhaseId, isFinishedGameStatus } from "@/util";

const canVoteOn = (proposal: DrawProposal) =>
  proposal.status === "pending" &&
  proposal.myVote !== null &&
  proposal.myVote.accepted === null;

const getWaitingDescription = (proposal: DrawProposal) => {
  if (canVoteOn(proposal)) {
    return `${proposal.acceptedCount} of ${proposal.totalVotes} accepted`;
  }
  return `Waiting for ${proposal.pendingCount} ${proposal.pendingCount === 1 ? "player" : "players"}`;
};

const getStatusDisplay = (proposal: DrawProposal) => {
  switch (proposal.status) {
    case "pending":
      return {
        icon: Handshake,
        title: proposal.createdBy.isCurrentUser
          ? "Draw proposed by you"
          : `Draw proposed by ${proposal.createdBy.nation}`,
        description: getWaitingDescription(proposal),
        highlighted: true,
      };
    case "accepted":
      return {
        icon: Handshake,
        title: "Draw accepted",
        description: "The game ended in a draw",
        highlighted: true,
      };
    case "rejected":
      return {
        icon: Ban,
        title: "Draw rejected",
        description: proposal.phaseName,
        highlighted: false,
      };
    case "cancelled":
      return {
        icon: Undo2,
        title: "Draw cancelled",
        description: proposal.phaseName,
        highlighted: false,
      };
    default:
      return {
        icon: Clock,
        title: "Draw expired",
        description: proposal.phaseName,
        highlighted: false,
      };
  }
};

interface PendingVote {
  proposal: DrawProposal;
  accepted: boolean;
}

interface ProposalRowProps {
  proposal: DrawProposal;
  onVote: (accepted: boolean) => void;
  onCancel: () => void;
  isCancelling: boolean;
}

const ProposalRow: React.FC<ProposalRowProps> = ({
  proposal,
  onVote,
  onCancel,
  isCancelling,
}) => {
  const {
    icon: Icon,
    title,
    description,
    highlighted,
  } = getStatusDisplay(proposal);
  const canCancel =
    proposal.status === "pending" && proposal.createdBy.isCurrentUser;

  return (
    <div className="flex flex-col gap-3 p-3">
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex size-12 shrink-0 items-center justify-center rounded-full ring-3 ring-border",
            highlighted
              ? "bg-amber-400 text-black"
              : "bg-muted text-muted-foreground"
          )}
        >
          <Icon className="size-5" />
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="font-semibold leading-tight">{title}</span>
          <p className="text-sm text-muted-foreground">{description}</p>
          {proposal.status === "pending" && (
            <p className="text-sm text-muted-foreground">
              Expires when the phase resolves
            </p>
          )}
        </div>
      </div>
      {canVoteOn(proposal) && (
        <div className="flex gap-2">
          <Button className="flex-1" onClick={() => onVote(true)}>
            <Check />
            Accept
          </Button>
          <Button
            className="flex-1"
            variant="outline"
            onClick={() => onVote(false)}
          >
            <X />
            Reject
          </Button>
        </div>
      )}
      {canCancel && (
        <Button variant="outline" onClick={onCancel} disabled={isCancelling}>
          Cancel proposal
        </Button>
      )}
    </div>
  );
};

const getVoteConfirmation = ({ proposal, accepted }: PendingVote) => {
  if (!accepted) {
    return {
      title: "Reject draw",
      description:
        "The proposal fails for everyone and the game continues. You can't change your vote.",
      confirmLabel: "Reject",
    };
  }
  return {
    title: "Accept draw",
    description:
      proposal.pendingCount === 1
        ? "Every other player has accepted. The game ends now in a draw shared by all surviving players."
        : "If every player accepts, the game ends in a draw shared by all surviving players. You can't change your vote.",
    confirmLabel: "Accept",
  };
};

const DrawProposalsScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pendingVote, setPendingVote] = useState<PendingVote | null>(null);

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: proposals } = useGamesDrawProposalsListSuspense(gameId);
  const voteMutation = useGamesDrawProposalsVotePartialUpdate();
  const cancelMutation = useGamesDrawProposalsCancelDestroy();

  const currentMember = game.members.find(m => m.isCurrentUser);
  const currentPhaseId = getCurrentPhaseId(game);

  const handleVote = async ({ proposal, accepted }: PendingVote) => {
    try {
      await voteMutation.mutateAsync({
        gameId: gameId,
        proposalId: proposal.id,
        data: { accepted },
      });
      queryClient.invalidateQueries({
        queryKey: getGamesDrawProposalsListQueryKey(gameId),
      });
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
    } catch {
      toast.error("Failed to vote");
    }
  };

  const handleCancel = async (proposalId: number) => {
    try {
      await cancelMutation.mutateAsync({
        gameId: gameId,
        proposalId: proposalId,
      });
      queryClient.invalidateQueries({
        queryKey: getGamesDrawProposalsListQueryKey(gameId),
      });
    } catch {
      toast.error("Failed to cancel proposal");
    }
  };

  const proposeDrawPath = `/game/${gameId}/phase/${phaseId}/propose-draw`;
  const hasPendingProposal = proposals.some(p => p.status === "pending");
  const hasProposedThisPhase = proposals.some(
    p =>
      p.phaseId === currentPhaseId &&
      p.createdBy.id === currentMember?.id &&
      p.status !== "cancelled"
  );
  const canProposeDraw =
    !!currentMember &&
    !game.sandbox &&
    !isFinishedGameStatus(game.status) &&
    !hasPendingProposal &&
    !hasProposedThisPhase;

  const confirmation = pendingVote ? getVoteConfirmation(pendingVote) : null;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Draw Proposals"
        variant="secondary"
        onNavigateBack={() =>
          navigate(`/game/${gameId}/phase/${phaseId}/orders`)
        }
        rightButton={
          canProposeDraw ? (
            <Button
              variant="outline"
              size="icon"
              aria-label="Propose draw"
              asChild
            >
              <Link to={proposeDrawPath}>
                <Handshake />
              </Link>
            </Button>
          ) : undefined
        }
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4">
            {proposals.length === 0 ? (
              <Notice
                icon={Handshake}
                title="No draw proposals"
                className="h-full"
              />
            ) : (
              <Card className="shrink-0 overflow-hidden py-0">
                <CardContent className="flex flex-col divide-y p-0">
                  {proposals.map(proposal => (
                    <ProposalRow
                      key={proposal.id}
                      proposal={proposal}
                      onVote={accepted =>
                        setPendingVote({ proposal, accepted })
                      }
                      onCancel={() => handleCancel(proposal.id)}
                      isCancelling={cancelMutation.isPending}
                    />
                  ))}
                </CardContent>
              </Card>
            )}
            {canProposeDraw && (
              <Button className="w-full" size="lg" asChild>
                <Link to={proposeDrawPath}>
                  <Handshake />
                  Propose Draw
                </Link>
              </Button>
            )}
          </Panel.Content>
        </Panel>
      </div>
      <AlertDialog
        open={pendingVote !== null}
        onOpenChange={open => !open && setPendingVote(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmation?.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmation?.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              disabled={voteMutation.isPending}
              onClick={() => pendingVote && handleVote(pendingVote)}
            >
              {confirmation?.confirmLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

const DrawProposalsScreenSkeleton: React.FC = () => (
  <div className="flex flex-col flex-1 min-h-0">
    <GameDetailAppBar title="Draw Proposals" variant="secondary" />
    <div className="flex-1 overflow-y-auto">
      <Panel>
        <Panel.Content className="flex flex-col gap-4 px-3 py-4">
          <Card className="shrink-0 overflow-hidden py-0">
            <CardContent className="flex flex-col divide-y p-0">
              {[0, 1].map(index => (
                <div key={index} className="flex items-center gap-3 p-3">
                  <Skeleton className="size-12 rounded-full" />
                  <div className="flex flex-1 flex-col gap-2">
                    <Skeleton className="h-4 w-40" />
                    <Skeleton className="h-4 w-28" />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </Panel.Content>
      </Panel>
    </div>
  </div>
);

const DrawProposalsScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<DrawProposalsScreenSkeleton />}>
      <DrawProposalsScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { DrawProposalsScreenSuspense as DrawProposalsScreen };
