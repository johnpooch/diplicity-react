import React, { Suspense, useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { Handshake, Info } from "lucide-react";
import { useRequiredParams } from "@/hooks";
import { useQueryClient } from "@tanstack/react-query";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { NationFlag } from "@/components/NationFlag";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Item,
  ItemContent,
  ItemTitle,
  ItemDescription,
  ItemGroup,
  ItemSeparator,
  ItemActions,
  ItemMedia,
} from "@/components/ui/item";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "../../components/Panel";
import {
  useGameRetrieveSuspense,
  useGamesDrawProposalsCreateCreate,
  getGamesDrawProposalsListQueryKey,
  useGamePhaseRetrieveSuspense,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";

const ProposeDrawScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: phase } = useGamePhaseRetrieveSuspense(gameId, Number(phaseId));
  const { data: variants } = useVariantsListSuspense();
  const createProposalMutation = useGamesDrawProposalsCreateCreate();

  const variant = variants.find(v => v.id === game.variantId);
  const victoryThreshold = variant?.soloVictoryScCount ?? 18;

  const currentMember = game.members.find(m => m.isCurrentUser);
  const activeMembers = game.members.filter(m => !m.eliminated && !m.kicked);

  React.useEffect(() => {
    if (currentMember && !selectedMembers.includes(currentMember.id)) {
      setSelectedMembers([currentMember.id]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when currentMember.id changes
  }, [currentMember?.id]);

  const getSupplyCenterCount = useCallback((nation: string | null) => {
    if (!nation) return 0;
    return phase.supplyCenters.filter(sc => sc.nation.name === nation).length;
  }, [phase.supplyCenters]);

  const combinedScCount = useMemo(() => {
    return selectedMembers.reduce((sum, memberId) => {
      const member = game.members.find(m => m.id === memberId);
      return sum + (member ? getSupplyCenterCount(member.nation) : 0);
    }, 0);
  }, [selectedMembers, game.members, getSupplyCenterCount]);

  const handleToggle = (memberId: number) => {
    if (currentMember && memberId === currentMember.id) {
      return;
    }
    setSelectedMembers(prevSelected =>
      prevSelected.includes(memberId)
        ? prevSelected.filter(id => id !== memberId)
        : [...prevSelected, memberId]
    );
  };

  const handleSubmit = async () => {
    try {
      await createProposalMutation.mutateAsync({
        gameId: gameId,
        data: {
          includedMemberIds: selectedMembers,
        },
      });
      toast.success("Draw proposal created");
      queryClient.invalidateQueries({
        queryKey: getGamesDrawProposalsListQueryKey(gameId),
      });
      navigate(`/game/${gameId}/phase/${phaseId}/draw-proposals`);
    } catch {
      toast.error("Failed to create proposal");
    }
  };

  const handleBack = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/orders`);
  };

  const isSubmitting = createProposalMutation.isPending;
  const meetsThreshold = combinedScCount >= victoryThreshold;
  const hasEnoughPlayers = selectedMembers.length >= 2;
  const canSubmit = meetsThreshold && hasEnoughPlayers && !isSubmitting;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Propose Draw"
        variant="secondary"
        onNavigateBack={handleBack}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Alert className="border-x-0 border-t-0 rounded-none bg-transparent">
            <Info className="size-4" />
            <AlertDescription>
              Select players to include in the draw. All players must accept for
              the draw to pass. If accepted, the game ends and only included
              players receive a draw victory.
            </AlertDescription>
          </Alert>
          <Panel.Content>
            <ItemGroup>
              {activeMembers.map(member => {
                const scCount = getSupplyCenterCount(member.nation);
                const isCurrentUser = member.isCurrentUser;
                return (
                  <React.Fragment key={member.id}>
                    <Item
                      className={`cursor-pointer hover:bg-accent/50 ${
                        isCurrentUser ? "bg-accent/30" : ""
                      }`}
                      onClick={() => handleToggle(member.id)}
                    >
                      <ItemMedia>
                        <NationFlag
                          nation={member.nation ?? ""}
                          variantId={variant?.id ?? ""}
                          size="md"
                          className="size-10"
                        />
                      </ItemMedia>
                      <ItemContent>
                        <ItemTitle>{member.nation}</ItemTitle>
                        <ItemDescription>
                          {member.name} ({scCount} SCs)
                        </ItemDescription>
                      </ItemContent>
                      <ItemActions>
                        <Checkbox
                          checked={selectedMembers.includes(member.id)}
                          disabled={isSubmitting || isCurrentUser}
                        />
                      </ItemActions>
                    </Item>
                    <ItemSeparator />
                  </React.Fragment>
                );
              })}
            </ItemGroup>
          </Panel.Content>
          <Separator />
          <Panel.Footer>
            <div className="flex flex-col gap-2 w-full">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Combined SCs:</span>
                <span
                  className={meetsThreshold ? "text-green-600" : "text-red-600"}
                >
                  {combinedScCount} / {victoryThreshold}
                </span>
              </div>
              {!meetsThreshold && (
                <p className="text-sm text-red-600">
                  Combined SCs must meet the victory threshold
                </p>
              )}
              {!hasEnoughPlayers && (
                <p className="text-sm text-red-600">
                  Select at least 2 players for a draw
                </p>
              )}
              <Button disabled={!canSubmit} onClick={handleSubmit}>
                <Handshake className="mr-2 h-4 w-4" />
                Propose Draw
              </Button>
            </div>
          </Panel.Footer>
        </Panel>
      </div>
    </div>
  );
};

const ProposeDrawScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <ProposeDrawScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { ProposeDrawScreenSuspense as ProposeDrawScreen };
