import React, { Suspense, useState } from "react";
import { useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import { cn } from "@/lib/utils";
import { useGameVariant } from "@/hooks/useGameVariant";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "../../components/Panel";
import {
  getGamesChannelsListQueryKey,
  useGameRetrieveSuspense,
  useGamesChannelsCreateCreate,
  type Channel,
  type Member,
} from "@/api/generated/endpoints";

const roleLabel = (member: Member): string | undefined => {
  if (member.isGameCreator) return "game creator";
  if (member.isBot) return "bot";
  return undefined;
};

const MemberRow: React.FC<{
  member: Member;
  nationFlagUrl: string | null;
  nationColor: string | null;
  selected: boolean;
  disabled: boolean;
  onToggle: () => void;
}> = ({ member, nationFlagUrl, nationColor, selected, disabled, onToggle }) => {
  const role = roleLabel(member);
  const nation = member.nation ?? member.name;

  return (
    <Card
      className={cn(
        "overflow-hidden py-0 transition-colors hover:bg-accent/50",
        selected && "bg-accent/50"
      )}
    >
      <CardContent className="p-0">
        <label className="flex w-full cursor-pointer items-center gap-3 p-3">
          <div className="relative size-12 shrink-0">
            <NationFlag
              flagUrl={nationFlagUrl}
              alt={nation}
              size="lg"
              className="size-12"
              color={nationColor}
            />
            <span className="absolute -bottom-0.5 -right-0.5">
              <Avatar className="size-5 ring-2 ring-card">
                <AvatarImage src={member.picture ?? undefined} />
                <AvatarFallback className="text-[8px]">
                  {member.name[0]?.toUpperCase() ?? "?"}
                </AvatarFallback>
              </Avatar>
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate font-semibold leading-tight">{nation}</p>
            <p className="truncate text-sm text-muted-foreground">
              {member.name}
              {role && ` (${role})`}
            </p>
          </div>
          <Checkbox
            checked={selected}
            onCheckedChange={onToggle}
            disabled={disabled}
            aria-label={`Select ${nation}`}
          />
        </label>
      </CardContent>
    </Card>
  );
};

const ChannelCreateScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);

  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const variantNations = variant?.nations ?? [];
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
      queryClient.setQueryData<Channel[]>(
        getGamesChannelsListQueryKey(gameId),
        (old) => [...(old ?? []), response]
      );
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
        title="Create channel"
        variant="secondary"
        onNavigateBack={handleBack}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4">
            <section className="flex flex-col gap-2">
              <h2 className="text-sm font-medium text-muted-foreground">Members</h2>
              <div className="flex flex-col gap-2">
                {game.members
                  .filter(m => !m.isCurrentUser && !m.kicked)
                  .map(member => (
                    <MemberRow
                      key={member.id}
                      member={member}
                      nationFlagUrl={findNationFlagUrl(variantNations, member.nation)}
                      nationColor={findNationColor(variantNations, member.nation)}
                      selected={selectedMembers.includes(member.id)}
                      disabled={isSubmitting}
                      onToggle={() => handleToggle(member.id)}
                    />
                  ))}
              </div>
            </section>
            <Button
              className="w-full"
              size="lg"
              disabled={selectedMembers.length === 0 || isSubmitting}
              onClick={handleCreateChannel}
            >
              Create channel
            </Button>
          </Panel.Content>
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
