import React, { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { NationFlag } from "@/components/NationFlag";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  useGameRetrieveSuspense,
  useGameMemberNationPreferenceRetrieveSuspense,
  useGameMemberNationPreferenceUpdate,
  getGameRetrieveQueryKey,
  getGameMemberNationPreferenceRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useRequiredParams } from "@/hooks";

export const NationPreferenceContent: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const { data: preference } = useGameMemberNationPreferenceRetrieveSuspense(gameId);
  const queryClient = useQueryClient();
  const updateMutation = useGameMemberNationPreferenceUpdate();

  const [rankedIds, setRankedIds] = useState<string[]>(preference.nationIds);

  const playableNations = variant
    ? variant.nations.filter(n => !n.nonPlayable)
    : [];

  const toggleNation = (nationId: string) => {
    setRankedIds(current =>
      current.includes(nationId)
        ? current.filter(id => id !== nationId)
        : [...current, nationId]
    );
  };

  const handleSave = async () => {
    try {
      await updateMutation.mutateAsync({
        gameId,
        data: { nationIds: rankedIds },
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGameRetrieveQueryKey(gameId),
        }),
        queryClient.invalidateQueries({
          queryKey: getGameMemberNationPreferenceRetrieveQueryKey(gameId),
        }),
      ]);
      toast.success("Nation preferences saved");
    } catch {
      toast.error("Failed to save nation preferences");
    }
  };

  return (
    <>
      <p className="text-sm text-muted-foreground">
        Tap nations in the order you would most like to play them. If all your
        ranked nations are taken, one of the unranked nations may still be
        assigned to you when the game starts.
      </p>

      <ScreenCard>
        <ScreenCardContent className="divide-y">
          {playableNations.map(n => {
            const rank = rankedIds.indexOf(n.nationId);
            return (
              <button
                key={n.nationId}
                onClick={() => toggleNation(n.nationId)}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0 w-full text-left"
                aria-pressed={rank !== -1}
              >
                <NationFlag
                  flagUrl={n.flagUrl}
                  alt={n.name}
                  size="lg"
                  className="size-8"
                  color={n.color}
                />
                <span className="flex-1 font-medium">{n.name}</span>
                {rank !== -1 ? (
                  <Badge>{rank + 1}</Badge>
                ) : (
                  <div className="size-5 rounded-full border border-dashed border-muted-foreground/50" />
                )}
              </button>
            );
          })}
        </ScreenCardContent>
      </ScreenCard>

      <Button
        onClick={handleSave}
        disabled={updateMutation.isPending}
        className="w-full"
      >
        Save preferences
      </Button>
    </>
  );
};
