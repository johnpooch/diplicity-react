import React, { Suspense } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { toast } from "sonner";
import { Check, X, Handshake, Plus, MoreVertical, Ban } from "lucide-react";
import { useRequiredParams } from "@/hooks";
import { useQueryClient } from "@tanstack/react-query";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import {
  Item,
  ItemContent,
  ItemTitle,
  ItemDescription,
  ItemGroup,
} from "@/components/ui/item";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
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
  useVariantsListSuspense,
} from "@/api/generated/endpoints";
import type {
  DrawProposal,
  GameRetrieve,
  Member,
  Variant,
} from "@/api/generated/endpoints";

type TabValue = "active" | "rejected";

interface ProposalItemProps {
  proposal: DrawProposal;
  game: GameRetrieve;
  currentMember: Member | undefined;
  variant: Variant | undefined;
  hasNationFlags: boolean;
  onVote: (proposalId: number, accepted: boolean) => void;
  onCancel: (proposalId: number) => void;
  isVoting: boolean;
  isCancelling: boolean;
}

const ProposalItem: React.FC<ProposalItemProps> = ({
  proposal,
  game,
  currentMember,
  variant,
  hasNationFlags,
  onVote,
  onCancel,
  isVoting,
  isCancelling,
}) => {
  const canVote =
    proposal.status === "pending" &&
    proposal.myVote !== null &&
    proposal.myVote.accepted === null;
  const isProposer = proposal.createdBy.id === currentMember?.id;
  const includedMembers = proposal.includedMemberIds
    .map(id => game.members.find(m => m.id === id))
    .filter((m): m is Member => Boolean(m));

  const isGm = game.nonPlayingGm && proposal.createdBy.nation == null;
  const flagUrl = isGm
    ? (hasNationFlags ? (proposal.createdBy.picture ?? null) : null)
    : (variant ? findNationFlagUrl(variant.nations, proposal.createdBy.nation) : null);
  const nationColor = isGm
    ? null
    : (variant ? findNationColor(variant.nations, proposal.createdBy.nation) : null);

  return (
    <Item className="border-b border-b-border">
      <NationFlag
        flagUrl={flagUrl}
        alt={proposal.createdBy.nation ?? proposal.createdBy.name}
        size="md"
        className="size-8 self-start"
        color={nationColor}
      />
      <ItemContent>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ItemTitle>Proposed by {proposal.createdBy.nation ?? proposal.createdBy.name}</ItemTitle>
            {proposal.status === "accepted" && (
              <Badge variant="default" className="bg-green-600">
                <Check className="mr-1 h-3 w-3" />
                Accepted
              </Badge>
            )}
            {proposal.status === "rejected" && (
              <Badge variant="destructive">
                <Ban className="mr-1 h-3 w-3" />
                Rejected
              </Badge>
            )}
          </div>
          {isProposer && proposal.status === "pending" && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={() => onCancel(proposal.id)}
                  disabled={isCancelling}
                >
                  Cancel Draw Proposal
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
        <ItemDescription>
          {includedMembers.map(m => m.nation).join(", ")}
        </ItemDescription>
        <div className="text-sm text-muted-foreground">
          {proposal.acceptedCount} of {proposal.totalVotes} accepted
        </div>
        {proposal.myVote && proposal.myVote.accepted !== null && (
          <div className="text-sm">
            Your vote:{" "}
            {proposal.myVote.accepted ? (
              <span className="text-green-600">Accepted</span>
            ) : (
              <span className="text-red-600">Rejected</span>
            )}
          </div>
        )}
        {canVote && (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => onVote(proposal.id, true)}
              disabled={isVoting}
            >
              <Check className="mr-1 h-4 w-4" />
              Accept
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onVote(proposal.id, false)}
              disabled={isVoting}
            >
              <X className="mr-1 h-4 w-4" />
              Reject
            </Button>
          </div>
        )}
      </ItemContent>
    </Item>
  );
};

const DrawProposalsScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const tab = (searchParams.get("tab") as TabValue) || "active";
  const setTab = (value: TabValue) => {
    setSearchParams({ tab: value });
  };

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: proposals } = useGamesDrawProposalsListSuspense(gameId);
  const { data: variants } = useVariantsListSuspense();
  const voteMutation = useGamesDrawProposalsVotePartialUpdate();
  const cancelMutation = useGamesDrawProposalsCancelDestroy();

  const variant = variants.find(v => v.id === game.variantId);
  const hasNationFlags = variant?.nations.some(n => n.flagUrl != null) ?? false;
  const currentMember = game.members.find(m => m.isCurrentUser);

  const handleVote = async (proposalId: number, accepted: boolean) => {
    try {
      await voteMutation.mutateAsync({
        gameId: gameId,
        proposalId: proposalId,
        data: { accepted },
      });
      toast.success(accepted ? "Draw proposal accepted" : "Draw proposal rejected");
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
      toast.success("Proposal cancelled");
      queryClient.invalidateQueries({
        queryKey: getGamesDrawProposalsListQueryKey(gameId),
      });
    } catch {
      toast.error("Failed to cancel proposal");
    }
  };

  const handleBack = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/orders`);
  };

  const handleProposeDraw = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/propose-draw`);
  };

  const activeProposals = proposals.filter(
    p => p.status === "pending" || p.status === "accepted"
  );
  const rejectedProposals = proposals.filter(p => p.status === "rejected");

  const hasActiveProposalByCurrentUser = activeProposals.some(
    p => p.status === "pending" && p.createdBy.id === currentMember?.id
  );
  const isGameCompleted = game.status === "completed";
  const canProposeDraw = !game.sandbox && !hasActiveProposalByCurrentUser && !isGameCompleted;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Draw Proposals"
        variant="secondary"
        onNavigateBack={handleBack}
        rightButton={
          canProposeDraw ? (
            <Button variant="outline" onClick={handleProposeDraw}>
              <Plus />
              New proposal
            </Button>
          ) : undefined
        }
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <Tabs value={tab} onValueChange={value => setTab(value as TabValue)}>
              <TabsList className="w-full">
                <TabsTrigger value="active" className="flex-1">
                  Active
                </TabsTrigger>
                <TabsTrigger value="rejected" className="flex-1">
                  Rejected
                </TabsTrigger>
              </TabsList>
              <TabsContent value="active">
                {activeProposals.length === 0 ? (
                  <Notice
                    icon={Handshake}
                    title="No active proposals"
                    message="There are no pending draw proposals for this phase."
                  />
                ) : (
                  <ItemGroup>
                    {activeProposals.map(proposal => (
                      <ProposalItem
                        key={proposal.id}
                        proposal={proposal}
                        game={game}
                        currentMember={currentMember}
                        variant={variant}
                        hasNationFlags={hasNationFlags}
                        onVote={handleVote}
                        onCancel={handleCancel}
                        isVoting={voteMutation.isPending}
                        isCancelling={cancelMutation.isPending}
                      />
                    ))}
                  </ItemGroup>
                )}
              </TabsContent>
              <TabsContent value="rejected">
                {rejectedProposals.length === 0 ? (
                  <Notice
                    icon={Ban}
                    title="No rejected proposals"
                    message="There are no rejected draw proposals for this phase."
                  />
                ) : (
                  <ItemGroup>
                    {rejectedProposals.map(proposal => (
                      <ProposalItem
                        key={proposal.id}
                        proposal={proposal}
                        game={game}
                        currentMember={currentMember}
                        variant={variant}
                        hasNationFlags={hasNationFlags}
                        onVote={handleVote}
                        onCancel={handleCancel}
                        isVoting={voteMutation.isPending}
                        isCancelling={cancelMutation.isPending}
                      />
                    ))}
                  </ItemGroup>
                )}
              </TabsContent>
            </Tabs>
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const DrawProposalsScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <DrawProposalsScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { DrawProposalsScreenSuspense as DrawProposalsScreen };
