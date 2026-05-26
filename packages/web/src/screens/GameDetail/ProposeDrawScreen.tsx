import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { Handshake, Info } from "lucide-react";
import { useRequiredParams } from "@/hooks";
import { useQueryClient } from "@tanstack/react-query";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { NationFlag, findNationFlagUrl } from "@/components/NationFlag";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Item,
  ItemContent,
  ItemTitle,
  ItemDescription,
  ItemGroup,
  ItemSeparator,
  ItemMedia,
} from "@/components/ui/item";
import { CivilDisorderBadge } from "@/components/CivilDisorderBadge";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "../../components/Panel";
import {
  useGameRetrieveSuspense,
  useGamesDrawProposalsCreateCreate,
  getGamesDrawProposalsListQueryKey,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";

const ProposeDrawScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: variants } = useVariantsListSuspense();
  const createProposalMutation = useGamesDrawProposalsCreateCreate();

  const variant = variants.find(v => v.id === game.variantId);
  const activeMembers = game.members.filter(m => !m.eliminated && !m.kicked);
  const includedMembers = activeMembers.filter(m => !m.civilDisorder);
  const cdMembers = activeMembers.filter(m => m.civilDisorder);

  const handleSubmit = async () => {
    try {
      await createProposalMutation.mutateAsync({
        gameId: gameId,
        data: {},
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
              All surviving players are automatically included in the draw. The
              proposal passes only if every active player accepts. Civil
              disorder players auto-accept but do not share in the victory.
            </AlertDescription>
          </Alert>
          <Panel.Content>
            <ItemGroup>
              {includedMembers.map(member => (
                <React.Fragment key={member.id}>
                  <Item>
                    <ItemMedia>
                      <NationFlag
                        flagUrl={variant ? findNationFlagUrl(variant.nations, member.nation) : null}
                        alt={member.nation ?? ""}
                        size="md"
                        className="size-10"
                      />
                    </ItemMedia>
                    <ItemContent>
                      <ItemTitle>{member.nation}</ItemTitle>
                      <ItemDescription>{member.name}</ItemDescription>
                    </ItemContent>
                  </Item>
                  <ItemSeparator />
                </React.Fragment>
              ))}
              {cdMembers.map(member => (
                <React.Fragment key={member.id}>
                  <Item className="opacity-60">
                    <ItemMedia>
                      <NationFlag
                        flagUrl={variant ? findNationFlagUrl(variant.nations, member.nation) : null}
                        alt={member.nation ?? ""}
                        size="md"
                        className="size-10"
                      />
                    </ItemMedia>
                    <ItemContent>
                      <ItemTitle className="flex items-center gap-2">
                        {member.nation}
                        <CivilDisorderBadge />
                      </ItemTitle>
                      <ItemDescription>
                        {member.name} (excluded from draw victory)
                      </ItemDescription>
                    </ItemContent>
                  </Item>
                  <ItemSeparator />
                </React.Fragment>
              ))}
            </ItemGroup>
          </Panel.Content>
          <Panel.Footer>
            <Button
              disabled={isSubmitting}
              onClick={handleSubmit}
              className="w-full"
            >
              <Handshake className="mr-2 h-4 w-4" />
              Propose Draw
            </Button>
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
