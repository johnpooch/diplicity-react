import React, { useState } from "react";
import { Check, Pencil, X } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { AccountSettingsCard } from "@/components/AccountSettingsCard";
import { CommitmentBadge } from "@/components/CommitmentBadge";
import { InfoButton } from "@/components/InfoButton";
import { NationFlag } from "@/components/NationFlag";
import { ProfilePictureEditor } from "@/components/ProfilePictureEditor";
import { useLogout } from "@/hooks/useLogout";
import {
  useUserRetrieveSuspense,
  useUserUpdatePartialUpdate,
  useUsersRetrieveSuspense,
  getUserRetrieveQueryKey,
  getUsersRetrieveQueryKey,
  type OutcomeEnum,
} from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId?: number;
  showAccountSettings?: boolean;
}

const formatPercent = (rate: number) => `${Math.round(rate * 100)}%`;

const outcomeLabel: Record<OutcomeEnum, string> = {
  won: "Won",
  drew: "Drew",
  eliminated: "Eliminated",
  survived: "Survived",
};

const outcomeVariant: Record<
  OutcomeEnum,
  "default" | "secondary" | "outline"
> = {
  won: "default",
  drew: "secondary",
  eliminated: "outline",
  survived: "outline",
};

interface StatTileProps {
  label: string;
  value: string | number;
  hint?: string;
  info?: string;
}

const StatTile: React.FC<StatTileProps> = ({ label, value, hint, info }) => (
  <div>
    <p className="text-2xl font-semibold tabular-nums">{value}</p>
    <span className="flex items-center gap-1 text-sm text-muted-foreground">
      {label}
      {info && <InfoButton label={label} text={info} />}
    </span>
    {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
  </div>
);

export const PlayerProfileContent: React.FC<PlayerProfileContentProps> = ({
  userId,
  showAccountSettings = false,
}) => {
  const queryClient = useQueryClient();
  const logout = useLogout();
  const { data: currentUser } = useUserRetrieveSuspense();
  const profileUserId = userId ?? currentUser.userId;
  const { data: profile } = useUsersRetrieveSuspense(profileUserId);
  const updateProfileMutation = useUserUpdatePartialUpdate();
  const isOwnProfile = profileUserId === currentUser.userId;

  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState("");
  const [saveNameError, setSaveNameError] = useState(false);

  const handleStartEditName = () => {
    setEditedName(profile.name);
    setSaveNameError(false);
    setIsEditingName(true);
  };

  const handleCancelEditName = () => {
    setIsEditingName(false);
    setEditedName("");
    setSaveNameError(false);
  };

  const handleSaveName = async () => {
    const trimmedName = editedName.trim();
    if (trimmedName.length >= 2) {
      try {
        await updateProfileMutation.mutateAsync({
          data: { name: trimmedName },
        });
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getUserRetrieveQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getUsersRetrieveQueryKey(profileUserId),
          }),
        ]);
        setIsEditingName(false);
        setEditedName("");
        setSaveNameError(false);
      } catch {
        setSaveNameError(true);
      }
    }
  };

  return (
    <>
      <Card>
        <CardContent className="flex flex-col gap-4">
          <div className="flex items-center gap-4">
            {isOwnProfile ? (
              <ProfilePictureEditor
                userId={profileUserId}
                name={profile.name}
                picture={profile.picture}
              />
            ) : (
              <Avatar className="size-16">
                <AvatarImage src={profile.picture ?? undefined} />
                <AvatarFallback className="text-xl">
                  {profile.name[0]?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
            )}
            <div className="min-w-0 flex-1">
              {isEditingName ? (
                <div className="flex items-center gap-2">
                  <Input
                    value={editedName}
                    onChange={e => setEditedName(e.target.value)}
                    autoFocus
                    disabled={updateProfileMutation.isPending}
                    className="max-w-xs"
                    onKeyDown={e => {
                      if (e.key === "Enter") handleSaveName();
                      else if (e.key === "Escape") handleCancelEditName();
                    }}
                  />
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={handleSaveName}
                    disabled={
                      updateProfileMutation.isPending ||
                      !editedName ||
                      editedName.trim().length < 2
                    }
                    aria-label="Save"
                  >
                    <Check className="size-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={handleCancelEditName}
                    disabled={updateProfileMutation.isPending}
                    aria-label="Cancel"
                  >
                    <X className="size-4" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="truncate text-xl font-semibold">
                    {profile.name}
                  </h2>
                  {isOwnProfile && (
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={handleStartEditName}
                      aria-label="Edit name"
                    >
                      <Pencil className="size-4" />
                    </Button>
                  )}
                  <CommitmentBadge commitment={profile.commitment} />
                </div>
              )}
              {saveNameError && (
                <p className="text-sm text-destructive">
                  Failed to update name. Please try again.
                </p>
              )}
              <p className="text-sm text-muted-foreground">
                Joined{" "}
                {new Date(profile.createdAt).toLocaleDateString(undefined, {
                  year: "numeric",
                  month: "long",
                })}
              </p>
            </div>
            {isOwnProfile && (
              <Button variant="default" onClick={logout}>
                Log out
              </Button>
            )}
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatTile label="Games" value={profile.totalGames} />
            <StatTile
              label="Victory"
              value={profile.soloWins}
              hint={
                profile.totalGames > 0
                  ? `${formatPercent(profile.soloWins / profile.totalGames)} of games`
                  : undefined
              }
            />
            <StatTile label="Draws" value={profile.draws} />
            <StatTile
              label="Reliability"
              value={formatPercent(1 - profile.nmrRate)}
              info="How consistently this player submits orders, based on their last 10 rated phases."
            />
          </div>
        </CardContent>
      </Card>

      {isOwnProfile && showAccountSettings && <AccountSettingsCard />}

      {profile.favouriteNation && (
        <Card>
          <CardContent className="flex flex-col gap-3">
            <h2 className="font-semibold">Most played</h2>
            <div className="flex items-center gap-3">
              <NationFlag
                flagUrl={profile.favouriteNation.nation.flagUrl}
                color={profile.favouriteNation.nation.color}
                alt={profile.favouriteNation.nation.name}
                className="size-10"
              />
              <div>
                <p className="font-medium">
                  {profile.favouriteNation.nation.name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {profile.favouriteNation.gamesPlayed} of {profile.totalGames}{" "}
                  games
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {profile.recentResults.length > 0 && (
        <Card>
          <CardContent className="flex flex-col gap-3">
            <h2 className="font-semibold">Recent results</h2>
            <div className="flex flex-col gap-3">
              {profile.recentResults.map(result => (
                <div key={result.gameId} className="flex items-center gap-3">
                  <NationFlag
                    flagUrl={result.nation.flagUrl}
                    color={result.nation.color}
                    alt={result.nation.name}
                    className="size-10"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {result.gameName}
                    </p>
                    <p className="truncate text-sm text-muted-foreground">
                      {result.nation.name} ·{" "}
                      {new Date(result.finishedAt).toLocaleDateString(
                        undefined,
                        {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        }
                      )}
                    </p>
                  </div>
                  <Badge variant={outcomeVariant[result.outcome]}>
                    {outcomeLabel[result.outcome]}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
};
