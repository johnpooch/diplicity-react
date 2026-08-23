import React from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  useGameRetrieveSuspense,
  useGameMemberNationUpdate,
  useGameMemberNationDestroy,
  getGameRetrieveQueryKey,
  Member,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useRequiredParams } from "@/hooks";

const UNASSIGNED = "unassigned";

export const NationAssignmentContent: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const queryClient = useQueryClient();
  const assignMutation = useGameMemberNationUpdate();
  const clearMutation = useGameMemberNationDestroy();

  const playableNations = variant
    ? variant.nations.filter(n => !n.nonPlayable)
    : [];

  const nationIdByName = new Map(playableNations.map(n => [n.name, n.nationId]));

  const pinnedNationId = (member: Member) =>
    member.nation ? nationIdByName.get(member.nation) : undefined;

  const takenBy = (nationId: string) =>
    game.members.find(m => pinnedNationId(m) === nationId);

  const handleChange = async (member: Member, value: string) => {
    try {
      if (value === UNASSIGNED) {
        await clearMutation.mutateAsync({ gameId, memberId: member.id });
      } else {
        await assignMutation.mutateAsync({
          gameId,
          memberId: member.id,
          data: { nationId: value },
        });
      }
      await queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
    } catch {
      toast.error("Failed to update nation assignment");
    }
  };

  return (
    <>
      <p className="text-sm text-muted-foreground">
        Assigned nations are kept when the game starts. Players without an
        assignment get a nation based on their preferences when the game
        starts.
      </p>

      <ScreenCard>
        <ScreenCardContent className="divide-y">
          {game.members.map(member => (
            <div
              key={member.id}
              className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
            >
              <Avatar className="size-8">
                <AvatarImage src={member.picture ?? undefined} />
                <AvatarFallback>
                  {member.name[0]?.toUpperCase() ?? "?"}
                </AvatarFallback>
              </Avatar>
              <span className="flex-1 font-medium truncate">{member.name}</span>
              <Select
                value={pinnedNationId(member) ?? UNASSIGNED}
                onValueChange={value => handleChange(member, value)}
              >
                <SelectTrigger
                  className="w-40"
                  aria-label={`Nation for ${member.name}`}
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={UNASSIGNED}>Unassigned</SelectItem>
                  {playableNations.map(n => {
                    const holder = takenBy(n.nationId);
                    const taken = !!holder && holder.id !== member.id;
                    return (
                      <SelectItem
                        key={n.nationId}
                        value={n.nationId}
                        disabled={taken}
                      >
                        {taken ? `${n.name} (assigned)` : n.name}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          ))}
        </ScreenCardContent>
      </ScreenCard>
    </>
  );
};
