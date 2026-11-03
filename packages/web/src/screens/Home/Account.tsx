import React, { Suspense, useRef, useState } from "react";
import { AxiosError } from "axios";
import {
  Check,
  X,
  Pencil,
  ChevronRight,
  Camera,
  Loader2,
  LogOut,
  Trash2,
  Upload,
} from "lucide-react";
import { Link } from "react-router";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "@/theme/useTheme";
import { useLogout } from "@/hooks/useLogout";
import { useMessaging } from "@/hooks/useMessaging";
import { downscaleImage } from "@/utils/downscaleImage";
import {
  useUserRetrieveSuspense,
  useUserUpdatePartialUpdate,
  useUserPictureUpdate,
  useUserPictureDestroy,
  getUserRetrieveQueryKey,
  getUsersRetrieveQueryKey,
  UserProfilePicture,
} from "@/api/generated/endpoints";
import { useQueryClient } from "@tanstack/react-query";

const pictureErrorMessage = (error: unknown, fallback: string) => {
  const data = (error as AxiosError<{ picture?: string[]; detail?: string }>)
    .response?.data;
  return data?.picture?.[0] ?? data?.detail ?? fallback;
};

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({ title, children }) => (
  <section className="flex flex-col gap-2">
    <h2 className="text-sm font-medium text-muted-foreground">{title}</h2>
    <Card className="overflow-hidden py-0">
      <CardContent className="p-0">{children}</CardContent>
    </Card>
  </section>
);

interface ProfilePictureEditorProps {
  userId: number;
  name: string;
  picture: string | null;
}

const ProfilePictureEditor: React.FC<ProfilePictureEditorProps> = ({
  userId,
  name,
  picture,
}) => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadPictureMutation = useUserPictureUpdate();
  const removePictureMutation = useUserPictureDestroy();
  const [isUploading, setIsUploading] = useState(false);
  const isPending = isUploading || removePictureMutation.isPending;

  const refreshProfile = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: getUserRetrieveQueryKey() }),
      queryClient.invalidateQueries({
        queryKey: getUsersRetrieveQueryKey(userId),
      }),
    ]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const picture = await downscaleImage(file);
      await uploadPictureMutation.mutateAsync({
        data: { picture: picture as unknown as UserProfilePicture["picture"] },
      });
      await refreshProfile();
    } catch (error) {
      toast.error(pictureErrorMessage(error, "Failed to upload picture"));
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemove = async () => {
    try {
      await removePictureMutation.mutateAsync();
      await refreshProfile();
    } catch (error) {
      toast.error(pictureErrorMessage(error, "Failed to remove picture"));
    }
  };

  return (
    <div className="relative">
      <Avatar className="size-12">
        <AvatarImage src={picture ?? undefined} />
        <AvatarFallback>{name[0]?.toUpperCase()}</AvatarFallback>
      </Avatar>
      {isPending && (
        <div className="absolute inset-0 flex items-center justify-center rounded-full bg-background/70">
          <Loader2 className="size-4 animate-spin" />
        </div>
      )}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            size="icon"
            variant="secondary"
            disabled={isPending}
            aria-label="Change picture"
            className="absolute -bottom-1 -right-1 size-6 rounded-full border"
          >
            <Camera className="size-3" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onSelect={() => fileInputRef.current?.click()}>
            <Upload />
            {picture ? "Replace picture" : "Upload picture"}
          </DropdownMenuItem>
          {picture && (
            <DropdownMenuItem variant="destructive" onSelect={handleRemove}>
              <Trash2 />
              Remove picture
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        tabIndex={-1}
        aria-hidden
        onChange={event => {
          const file = event.target.files?.[0];
          if (file) handleUpload(file);
          event.target.value = "";
        }}
      />
    </div>
  );
};

const Account: React.FC = () => {
  const queryClient = useQueryClient();
  const logout = useLogout();
  const { data: userProfile } = useUserRetrieveSuspense();
  const updateProfileMutation = useUserUpdatePartialUpdate();

  const { preference, setPreference } = useTheme();

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
    <div className="space-y-4">
      <Card className="overflow-hidden py-0">
        <CardContent className="flex flex-col divide-y p-0">
          <div className="p-3">
            <div className="flex items-center gap-3">
              <ProfilePictureEditor
                userId={userProfile.userId}
                name={userProfile.name}
                picture={userProfile.picture}
              />
              {isEditingName ? (
                <>
                  <Input
                    value={editedName}
                    onChange={e => setEditedName(e.target.value)}
                    autoFocus
                    disabled={updateProfileMutation.isPending}
                    aria-label="Name"
                    className="flex-1"
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
                      editedName.trim().length < 2
                    }
                    aria-label="Save"
                  >
                    <Check />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={handleCancelEditName}
                    disabled={updateProfileMutation.isPending}
                    aria-label="Cancel"
                  >
                    <X />
                  </Button>
                </>
              ) : (
                <>
                  <h2 className="flex-1 truncate font-medium">
                    {userProfile.name}
                  </h2>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={handleStartEditName}
                    aria-label="Edit name"
                  >
                    <Pencil />
                  </Button>
                </>
              )}
            </div>
            {saveNameError && (
              <p className="mt-2 text-sm text-destructive">
                Failed to update name. Please try again.
              </p>
            )}
          </div>
          <Link
            to={`/player/${userProfile.userId}`}
            className="flex items-center justify-between gap-4 px-6 py-3 text-sm hover:bg-accent/50"
          >
            View my profile
            <ChevronRight className="size-4 text-muted-foreground" />
          </Link>
        </CardContent>
      </Card>

      <Section title="Appearance">
        <div className="flex items-center justify-between gap-4 px-6 py-3 text-sm">
          <Label htmlFor="theme-select">Theme</Label>
          <Select value={preference} onValueChange={setPreference}>
            <SelectTrigger id="theme-select" size="sm" className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="light">Light</SelectItem>
              <SelectItem value="dark">Dark</SelectItem>
              <SelectItem value="system">System</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Section>

      <Section title="Notifications">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between gap-4">
            <Label htmlFor="push-notifications">Push notifications</Label>
            <Switch
              id="push-notifications"
              checked={!permissionDenied && enabled}
              disabled={permissionDenied}
              onCheckedChange={handleTogglePushNotifications}
            />
          </div>
          {permissionDenied && (
            <p className="mt-1 text-sm text-muted-foreground">
              Reset permissions for this app or website before notifications can
              be turned on.
            </p>
          )}
          {error && <p className="mt-1 text-sm text-destructive">{error}</p>}
        </div>
      </Section>

      <div className="flex flex-col gap-4">
        <Button variant="outline" onClick={logout}>
          <LogOut />
          Log out
        </Button>
        <Button
          variant="outline"
          className="text-destructive hover:text-destructive"
          asChild
        >
          <Link to="/delete-account">
            <Trash2 />
            Delete account
          </Link>
        </Button>
      </div>
    </div>
  );
};

const AccountSkeleton: React.FC = () => (
  <div className="space-y-4">
    <Card className="overflow-hidden py-0">
      <CardContent className="flex flex-col divide-y p-0">
        <div className="flex items-center gap-3 p-3">
          <Skeleton className="size-12 rounded-full" />
          <Skeleton className="h-5 w-32" />
        </div>
        <div className="px-6 py-3">
          <Skeleton className="h-5 w-28" />
        </div>
      </CardContent>
    </Card>
    <Section title="Appearance">
      <Skeleton className="mx-6 my-3 h-8" />
    </Section>
    <Section title="Notifications">
      <Skeleton className="mx-6 my-3 h-5" />
    </Section>
    <div className="flex flex-col gap-4">
      <Skeleton className="h-9" />
      <Skeleton className="h-9" />
    </div>
  </div>
);

const AccountSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Account" />
      <QueryErrorBoundary>
        <Suspense fallback={<AccountSkeleton />}>
          <Account />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { AccountSuspense as Account };
