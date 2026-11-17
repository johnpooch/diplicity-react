import React, { useState } from "react";
import { Flag, Lock } from "lucide-react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { NationFlag } from "@/components/NationFlag";
import { Notice } from "@/components/Notice";
import { Badge } from "@/components/ui/badge";
import { PrimaryButton } from "@/components/ui/role-buttons";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  type GameRetrieve,
  useGameRetrieveSuspense,
  useGameMemberNationPreferenceRetrieveSuspense,
  useGameMemberNationPreferenceUpdate,
  getGameRetrieveQueryKey,
  getGameMemberNationPreferenceRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useRequiredParams } from "@/hooks";

interface NationPreferenceContentProps {
  savedPath: string;
}

interface NationPreferenceFormProps extends NationPreferenceContentProps {
  gameId: string;
  game: GameRetrieve;
}

const NationPreferenceForm: React.FC<NationPreferenceFormProps> = ({
  gameId,
  game,
  savedPath,
}) => {
  const navigate = useNavigate();
  const variant = useGameVariant(game);
  const { data: preference } =
    useGameMemberNationPreferenceRetrieveSuspense(gameId);
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
      navigate(savedPath);
    } catch {
      toast.error("Failed to save nation preferences");
    }
  };

  return (
    <>
      <p className="text-sm text-muted-foreground">
        Tap nations in the order you would most like to play them.
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

      <PrimaryButton
        onClick={handleSave}
        disabled={updateMutation.isPending}
        className="w-full"
      >
        Save preferences
      </PrimaryButton>
    </>
  );
};

export const NationPreferenceContent: React.FC<
  NationPreferenceContentProps
> = ({ savedPath }) => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { data: game } = useGameRetrieveSuspense(gameId);

  const assignedNation = game.members.find(m => m.isCurrentUser)?.nation;
  const canEditNationPreferences = game.playerListActions.some(
    action => action.key === "edit_nation_preferences"
  );

  if (assignedNation) {
    return (
      <Notice
        icon={Flag}
        title={`The Game Master assigned you ${assignedNation}`}
        message="Your nation is already set, so preferences do not apply to this game."
      />
    );
  }

  if (!canEditNationPreferences) {
    return (
      <Notice
        icon={Lock}
        title="Nation preferences are closed"
        message="This game has started, so preferences no longer apply."
      />
    );
  }

  return (
    <NationPreferenceForm gameId={gameId} game={game} savedPath={savedPath} />
  );
};
