import React, { useState } from "react";
import { Check, Info, Pencil, X } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { AccountSettingsCard } from "@/components/AccountSettingsCard";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { CommitmentBadge, COMMITMENT_TIERS } from "@/components/CommitmentBadge";
import { Input } from "@/components/ui/input";
import { ProfilePictureEditor } from "@/components/ProfilePictureEditor";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { useLogout } from "@/hooks/useLogout";
import {
  useUserRetrieveSuspense,
  useUserUpdatePartialUpdate,
  useUsersRetrieveSuspense,
  getUserRetrieveQueryKey,
  getUsersRetrieveQueryKey,
} from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId?: number;
  showAccountSettings?: boolean;
}

const formatPercent = (rate: number) => `${Math.round(rate * 100)}%`;

interface StatRowProps {
  label: string;
  value: string | number;
  info?: string;
}

const StatRow: React.FC<StatRowProps> = ({ label, value, info }) => (
  <div className="flex items-center justify-between py-2">
    <span className="text-sm text-muted-foreground flex items-center gap-1">
      {label}
      {info && (
        <Popover>
          <PopoverTrigger asChild>
            <button
              type="button"
              className="text-muted-foreground/60 hover:text-muted-foreground"
              aria-label={`What is ${label}?`}
            >
              <Info className="size-3.5" />
            </button>
          </PopoverTrigger>
          <PopoverContent className="text-sm">{info}</PopoverContent>
        </Popover>
      )}
    </span>
    <span className="text-sm font-medium">{value}</span>
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
    <div className="space-y-4">
      <ScreenCard>
        <ScreenCardContent>
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
                <AvatarFallback className="text-lg">
                  {profile.name[0]?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
            )}
            <div className="flex-1 min-w-0">
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
                  <span className="text-lg font-semibold">{profile.name}</span>
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
              <Button variant="outline" onClick={logout}>
                Log out
              </Button>
            )}
          </div>
        </ScreenCardContent>
      </ScreenCard>

      {isOwnProfile && showAccountSettings && <AccountSettingsCard />}

      <ScreenCard>
        <ScreenCardContent>
          <h3 className="text-sm font-semibold mb-2">Commitment</h3>
          <div className="divide-y">
            <StatRow
              label="Tier"
              value={COMMITMENT_TIERS[profile.commitment]?.label ?? profile.commitment}
              info={
                profile.commitment === "undefined"
                  ? "This player hasn't played enough rated phases to have a commitment rating yet. A rating appears after 10 rated phases."
                  : "How consistently this player submits orders, based on their last 10 rated phases."
              }
            />
            <StatRow
              label="NMR Rate"
              value={formatPercent(profile.nmrRate)}
              info="The percentage of movement phases where this player submitted no orders, based on their last 10 games."
            />
          </div>
        </ScreenCardContent>
      </ScreenCard>

      <ScreenCard>
        <ScreenCardContent>
          <h3 className="text-sm font-semibold mb-2">Games</h3>
          <div className="divide-y">
            <StatRow label="Total Games" value={profile.totalGames} />
            <StatRow label="Solo Wins" value={profile.soloWins} />
            <StatRow label="Draws" value={profile.draws} />
            <StatRow label="Losses" value={profile.losses} />
          </div>
        </ScreenCardContent>
      </ScreenCard>
    </div>
  );
};
