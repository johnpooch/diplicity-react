import React, { Suspense, useState } from "react";
import { Check, X, Pencil, MoreHorizontal } from "lucide-react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/auth";
import { useMessaging } from "@/hooks/useMessaging";
import {
  useUserRetrieveSuspense,
  useUserUpdatePartialUpdate,
  getUserRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { useQueryClient } from "@tanstack/react-query";

const Profile: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: userProfile } = useUserRetrieveSuspense();
  const updateProfileMutation = useUserUpdatePartialUpdate();

  const {
    enableMessaging,
    enabled,
    disableMessaging,
    permissionDenied,
    error,
  } = useMessaging();
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState("");
  const [saveNameError, setSaveNameError] = useState(false);

  const handleStartEditName = () => {
    setEditedName(userProfile?.name || "");
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
        queryClient.invalidateQueries({ queryKey: getUserRetrieveQueryKey() });
        setIsEditingName(false);
        setEditedName("");
        setSaveNameError(false);
      } catch {
        setSaveNameError(true);
      }
    }
  };

  const handleTogglePushNotifications = (checked: boolean) => {
    if (checked) {
      enableMessaging();
    } else {
      disableMessaging();
    }
  };

  return (
    <ScreenCard>
      <ScreenCardContent className="space-y-4">
        <h2 className="text-lg font-semibold">User</h2>
        <div className="flex items-center gap-4">
          <div>
            <Avatar className="size-12">
              <AvatarImage src={userProfile?.picture ?? undefined} />
              <AvatarFallback>
                {userProfile?.name?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
          </div>

          <div className="flex-1">
            {isEditingName ? (
              <div className="flex items-center gap-2">
                <Input
                  value={editedName}
                  onChange={e => setEditedName(e.target.value)}
                  autoFocus
                  disabled={updateProfileMutation.isPending}
                  className="max-w-xs"
                  onKeyDown={e => {
                    if (e.key === "Enter") {
                      handleSaveName();
                    } else if (e.key === "Escape") {
                      handleCancelEditName();
                    }
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
              <div className="flex items-center gap-2">
                <span className="text-lg font-medium">{userProfile?.name}</span>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={handleStartEditName}
                  aria-label="Edit name"
                >
                  <Pencil className="size-4" />
                </Button>
              </div>
            )}
            {saveNameError && (
              <p className="text-sm text-destructive mt-1">
                Failed to update name. Please try again.
              </p>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Notifications</h2>

          <div className="space-y-2">
            {permissionDenied && (
              <Alert>
                <AlertDescription>
                  Notifications are blocked in your browser. To enable them,
                  click the icon in your address bar and allow notifications.
                </AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Switch
                  id="push-notifications"
                  checked={enabled}
                  disabled={permissionDenied}
                  onCheckedChange={handleTogglePushNotifications}
                />
                <Label htmlFor="push-notifications">Push Notifications</Label>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>
          </div>
        </div>
      </ScreenCardContent>
    </ScreenCard>
  );
};

const ProfileSuspense: React.FC = () => {
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <ScreenContainer>
      <ScreenHeader
        title="Profile"
        actions={
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" aria-label="Menu">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        }
      />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <Profile />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { ProfileSuspense as Profile };
