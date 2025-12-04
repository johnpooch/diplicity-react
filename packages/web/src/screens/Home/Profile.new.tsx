import React, { useState } from "react";
import { useNavigate } from "react-router";
import { Check, X, Pencil, Menu as MenuIcon } from "lucide-react";

import { HomeLayout } from "@/components/HomeLayout";
import { Navigation } from "@/components/Navigation";
import { InfoPanel } from "@/components/InfoPanel.new";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { navigationItems } from "@/navigation/navigationItems";
import { authSlice, service } from "@/store";
import { useMessaging } from "@/context";
import { useDispatch } from "react-redux";

interface ProfileProps {
  isLoading: boolean;
  userProfile:
    | {
        name: string;
        picture: string | null;
      }
    | undefined;
  onUpdateName: (name: string) => Promise<void>;
  isSubmitting: boolean;
  pushNotificationsEnabled: boolean;
  pushNotificationsPermissionDenied: boolean;
  pushNotificationsError: string | undefined;
  onTogglePushNotifications: (enabled: boolean) => void;
  onLogout: () => void;
}

const Profile: React.FC<ProfileProps> = ({
  isLoading,
  userProfile,
  onUpdateName,
  isSubmitting,
  pushNotificationsEnabled,
  pushNotificationsPermissionDenied,
  pushNotificationsError,
  onTogglePushNotifications,
  onLogout,
}) => {
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
        await onUpdateName(trimmedName);
        setIsEditingName(false);
        setEditedName("");
        setSaveNameError(false);
      } catch {
        setSaveNameError(true);
      }
    }
  };
  return (
    <div className="w-full space-y-4">
      <h1 className="text-2xl font-bold">Profile</h1>

      <div className="space-y-6">
        {/* Profile Header */}
        <div className="flex items-center gap-4">
          <div>
            {isLoading ? (
              <Skeleton className="size-12 rounded-full" />
            ) : (
              <Avatar className="size-12">
                <AvatarImage src={userProfile?.picture ?? undefined} />
                <AvatarFallback>
                  {userProfile?.name?.[0]?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
            )}
          </div>

          <div className="flex-1">
            {isLoading ? (
              <Skeleton className="h-6 w-40" />
            ) : isEditingName ? (
              <div className="flex items-center gap-2">
                <Input
                  value={editedName}
                  onChange={e => setEditedName(e.target.value)}
                  autoFocus
                  disabled={isSubmitting}
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
                    isSubmitting || !editedName || editedName.trim().length < 2
                  }
                  aria-label="Save"
                >
                  <Check className="size-4" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={handleCancelEditName}
                  disabled={isSubmitting}
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

          <div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button size="icon" variant="ghost" aria-label="Menu">
                  <MenuIcon className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onLogout}>Logout</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        <Separator />

        {/* Notifications Section */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Notifications</h2>

          <div className="space-y-4">
            {pushNotificationsError && (
              <Alert variant="destructive">
                <AlertDescription>{pushNotificationsError}</AlertDescription>
              </Alert>
            )}

            {pushNotificationsPermissionDenied && !pushNotificationsError && (
              <Alert>
                <AlertDescription>
                  Notifications are blocked in your browser. To enable them,
                  click the icon in your address bar and allow notifications.
                </AlertDescription>
              </Alert>
            )}

            <div className="flex items-center space-x-2">
              <Switch
                id="push-notifications"
                checked={pushNotificationsEnabled}
                disabled={pushNotificationsPermissionDenied}
                onCheckedChange={onTogglePushNotifications}
              />
              <Label htmlFor="push-notifications">Push Notifications</Label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ProfileContainer: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const query = service.endpoints.userRetrieve.useQuery();
  const [updateProfile, updateProfileMutation] =
    service.endpoints.userUpdatePartialUpdate.useMutation();

  const {
    enableMessaging,
    enabled,
    disableMessaging,
    permissionDenied,
    error,
  } = useMessaging();

  const handleUpdateName = async (name: string) => {
    await updateProfile({
      patchedUserProfile: { name },
    }).unwrap();
  };

  const handleLogout = () => {
    dispatch(authSlice.actions.logout());
  };

  const handleTogglePushNotifications = (checked: boolean) => {
    if (checked) {
      enableMessaging();
    } else {
      disableMessaging();
    }
  };

  const navItems = navigationItems.map(item => ({
    ...item,
    isActive: item.path === "/profile",
  }));

  return (
    <HomeLayout
      left={
        <Navigation
          items={navItems}
          variant="sidebar"
          onItemClick={path => navigate(path)}
        />
      }
      center={
        <Profile
          isLoading={query.isLoading}
          userProfile={query.data}
          onUpdateName={handleUpdateName}
          isSubmitting={updateProfileMutation.isLoading}
          pushNotificationsEnabled={enabled}
          pushNotificationsPermissionDenied={permissionDenied}
          pushNotificationsError={error ?? undefined}
          onTogglePushNotifications={handleTogglePushNotifications}
          onLogout={handleLogout}
        />
      }
      right={<InfoPanel />}
      bottom={
        <Navigation
          items={navItems}
          variant="bottom"
          onItemClick={path => navigate(path)}
        />
      }
    />
  );
};

export { Profile, ProfileContainer };
export type { ProfileProps };
