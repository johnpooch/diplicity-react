import React, { Suspense, useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { UserPlus } from "lucide-react";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
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
  useGamesChannelsCreateCreate,
} from "@/api/generated/endpoints";

const ChannelCreateScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const navigate = useNavigate();
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);

  const { data: game } = useGameRetrieveSuspense(gameId);
  const createChannelMutation = useGamesChannelsCreateCreate();

  const handleToggle = (memberId: number) => {
    setSelectedMembers(prevSelected =>
      prevSelected.includes(memberId)
        ? prevSelected.filter(id => id !== memberId)
        : [...prevSelected, memberId]
    );
  };

  const handleCreateChannel = async () => {
    try {
      const response = await createChannelMutation.mutateAsync({
        gameId: gameId,
        data: {
          memberIds: selectedMembers,
        },
      });
      toast.success("Channel created successfully");
      if (response) {
        navigate(`/game/${gameId}/phase/${phaseId}/chat/channel/${response.id}`);
      }
    } catch {
      toast.error("Failed to create channel");
    }
  };

  const handleBack = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/chat`);
  };

  const isSubmitting = createChannelMutation.isPending;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Create Channel"
        variant="secondary"
        onNavigateBack={handleBack}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <ItemGroup>
              {game.members
                .filter(m => !m.isCurrentUser)
                .map(member => (
                  <React.Fragment key={member.nation}>
                    <Item
                      className="cursor-pointer hover:bg-accent/50"
                      onClick={() => handleToggle(member.id)}
                    >
                      <ItemMedia>
                        <Avatar>
                          <AvatarImage src={member.picture ?? undefined} />
                          <AvatarFallback>{member.nation?.[0]}</AvatarFallback>
                        </Avatar>
                      </ItemMedia>
                      <ItemContent>
                        <ItemTitle>{member.nation}</ItemTitle>
                        <ItemDescription>{member.name}</ItemDescription>
                      </ItemContent>
                      <ItemActions>
                        <Checkbox
                          checked={selectedMembers.includes(member.id)}
                          disabled={isSubmitting}
                        />
                      </ItemActions>
                    </Item>
                    <ItemSeparator />
                  </React.Fragment>
                ))}
            </ItemGroup>
          </Panel.Content>
          <Separator />
          <Panel.Footer>
            <div className="flex justify-end w-full">
              <Button
                disabled={selectedMembers.length === 0 || isSubmitting}
                onClick={handleCreateChannel}
              >
                <UserPlus />
                Select Members
              </Button>
            </div>
          </Panel.Footer>
        </Panel>
      </div>
    </div>
  );
};

const ChannelCreateScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <ChannelCreateScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { ChannelCreateScreenSuspense as ChannelCreateScreen };
