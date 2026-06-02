import React, { Suspense, useRef, useState } from "react";
import { Check, X, Pencil } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
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
import { Switch } from "@/components/ui/switch";
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useTheme } from "@/theme/useTheme";
import { useAuth } from "@/auth";
import { useNavigate } from "react-router";
import { useMessaging } from "@/hooks/useMessaging";
import {
  useUserRetrieveSuspense,
  useUserUpdatePartialUpdate,
  getUserRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { useQueryClient } from "@tanstack/react-query";

const COLOUR_PALETTE = [
  "#FFCDD2", "#F8BBD9", "#E1BEE7", "#BBDEFB", "#B2DFDB", "#DCEDC8", "#FFF9C4", "#F5F5F5",
  "#EF9A9A", "#F48FB1", "#CE93D8", "#90CAF9", "#80CBC4", "#AED581", "#FFF176", "#BDBDBD",
  "#EF5350", "#EC407A", "#AB47BC", "#42A5F5", "#26A69A", "#66BB6A", "#FFEE58", "#8D6E63",
  "#E53935", "#E91E63", "#9C27B0", "#2196F3", "#009688", "#4CAF50", "#FDD835", "#795548",
  "#C62828", "#AD1457", "#6A1B9A", "#1565C0", "#00695C", "#2E7D32", "#F57F17", "#4E342E",
  "#B71C1C", "#880E4F", "#4A148C", "#0D47A1", "#004D40", "#1B5E20", "#E65100", "#212121",
];

const HEX_PATTERN = /^#[0-9A-Fa-f]{6}$/;

const DEFAULT_COLOUR_PROFILE = [
  "#E63946", "#F4A261", "#E9C46A", "#2A9D8F", "#264653",
  "#457B9D", "#A8DADC", "#90BE6D", "#43AA8B", "#F94144",
  "#F3722C", "#F8961E", "#F9C74F", "#4D908E", "#277DA1",
  "#9D0208", "#3A0CA3", "#7B2D8B", "#C77DFF", "#48CAE4",
  "#023E8A", "#606C38", "#DDA15E", "#BC6C25", "#8B2FC9",
  "#5C4033", "#B5E48C", "#FF6B6B", "#4ECDC4", "#45B7D1",
];

const Profile: React.FC = () => {
  const queryClient = useQueryClient();
  const { logout } = useAuth();
  const navigate = useNavigate();
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

  const [colourProfileEnabled, setColourProfileEnabled] = useState(
    userProfile.colourProfileEnabled ?? false,
  );
  const savedColours: string[] =
    Array.isArray(userProfile.customColourProfile) &&
    userProfile.customColourProfile.length === 30
      ? userProfile.customColourProfile
      : DEFAULT_COLOUR_PROFILE;
  const [localColours, setLocalColours] = useState<string[]>(() => savedColours);
  const saveColourTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isDefaultColours = DEFAULT_COLOUR_PROFILE.every((c, i) => c === localColours[i]);

  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingColour, setEditingColour] = useState("#000000");
  const [hexInput, setHexInput] = useState("#000000");
  const isValidEditHex = HEX_PATTERN.test(hexInput);

  const handleSwatchClick = (index: number) => {
    setEditingIndex(index);
    setEditingColour(localColours[index]);
    setHexInput(localColours[index]);
  };

  const handlePickPreset = (colour: string) => {
    setEditingColour(colour);
    setHexInput(colour);
  };

  const handleHexInput = (value: string) => {
    setHexInput(value);
    if (HEX_PATTERN.test(value)) {
      setEditingColour(value);
    }
  };

  const handleApplyColour = () => {
    if (editingIndex !== null) {
      handleColourChange(editingIndex, editingColour);
    }
    setEditingIndex(null);
  };

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

  const handleToggleColourProfile = async (checked: boolean) => {
    setColourProfileEnabled(checked);
    try {
      await updateProfileMutation.mutateAsync({
        data: { colourProfileEnabled: checked },
      });
      queryClient.invalidateQueries({ queryKey: getUserRetrieveQueryKey() });
    } catch {
      setColourProfileEnabled(!checked);
    }
  };

  const handleColourChange = (index: number, colour: string) => {
    const next = localColours.map((c, i) => (i === index ? colour : c));
    setLocalColours(next);
    if (saveColourTimeoutRef.current) clearTimeout(saveColourTimeoutRef.current);
    saveColourTimeoutRef.current = setTimeout(() => {
      updateProfileMutation
        .mutateAsync({ data: { customColourProfile: next } })
        .then(() =>
          queryClient.invalidateQueries({ queryKey: getUserRetrieveQueryKey() }),
        )
        .catch(() => toast.error("Failed to save colour profile"));
    }, 600);
  };

  const handleResetColours = () => {
    setLocalColours(DEFAULT_COLOUR_PROFILE);
    if (saveColourTimeoutRef.current) clearTimeout(saveColourTimeoutRef.current);
    updateProfileMutation
      .mutateAsync({ data: { customColourProfile: DEFAULT_COLOUR_PROFILE } })
      .then(() =>
        queryClient.invalidateQueries({ queryKey: getUserRetrieveQueryKey() }),
      )
      .catch(() => toast.error("Failed to reset colour profile"));
  };

  return (
    <ScreenCard>
      <ScreenCardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">User</h2>
          <Button
            variant="outline"
            onClick={logout}
            className="hidden sm:inline-flex"
          >
            Log out
          </Button>
        </div>
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
        <Button
          variant="outline"
          onClick={logout}
          className="sm:hidden"
        >
          Log out
        </Button>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Appearance</h2>
          <div className="flex items-center gap-4">
            <Label htmlFor="theme-select">Theme</Label>
            <Select value={preference} onValueChange={setPreference}>
              <SelectTrigger id="theme-select" className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div
            className={cn(
              "rounded-lg border p-4 transition-all duration-300",
              colourProfileEnabled
                ? "border-border shadow-md"
                : "border-transparent shadow-none",
            )}
          >
            <div className="flex items-center space-x-2">
              <Switch
                id="colour-profile"
                checked={colourProfileEnabled}
                disabled={updateProfileMutation.isPending}
                onCheckedChange={handleToggleColourProfile}
              />
              <Label htmlFor="colour-profile">Custom colour profile</Label>
            </div>
            <div
              className={cn(
                "grid transition-all duration-300",
                colourProfileEnabled ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
              )}
            >
              <div className="overflow-hidden">
                <div className="mt-3 space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Nation colours will be replaced with these colours, in order,
                    across all variants.
                  </p>
                  <div className="grid grid-cols-6 gap-2">
                    {localColours.map((colour, i) => (
                      <div key={i} className="flex items-center gap-1">
                        <span className="text-xs text-muted-foreground w-4 text-right">
                          {i + 1}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleSwatchClick(i)}
                          className="size-8 rounded-full border border-border/40 transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1"
                          style={{ backgroundColor: colour }}
                          aria-label={`Colour ${i + 1}: ${colour}`}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleResetColours}
                      disabled={isDefaultColours || updateProfileMutation.isPending}
                    >
                      Reset to defaults
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Notifications</h2>

          <div className="space-y-2">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Switch
                  id="push-notifications"
                  checked={!permissionDenied && enabled}
                  disabled={permissionDenied}
                  onCheckedChange={handleTogglePushNotifications}
                />
                <Label htmlFor="push-notifications">Push Notifications</Label>
              </div>
              {permissionDenied && (
                <p className="text-sm text-muted-foreground">
                  Reset permissions for this app or website before notifications
                  can be turned on.
                </p>
              )}
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>
          </div>
        </div>

        <div className="pt-4 border-t">
          <Button
            variant="destructive"
            onClick={() => navigate("/delete-account")}
          >
            Delete Account
          </Button>
        </div>
      </ScreenCardContent>
      <Sheet
        open={editingIndex !== null}
        onOpenChange={open => { if (!open) setEditingIndex(null); }}
      >
        <SheetContent side="bottom">
          <SheetHeader>
            <SheetTitle>
              {editingIndex !== null ? `Colour ${editingIndex + 1}` : ""}
            </SheetTitle>
          </SheetHeader>
          <div className="px-4 space-y-4">
            <div className="flex items-center gap-3">
              <div
                className="size-10 rounded-full border border-border/40 shrink-0"
                style={{ backgroundColor: editingColour }}
              />
              <Input
                value={hexInput}
                onChange={e => handleHexInput(e.target.value)}
                placeholder="#000000"
                className={cn("font-mono", !isValidEditHex && hexInput !== "" && "border-destructive")}
              />
            </div>
            <div className="grid grid-cols-8 gap-2">
              {COLOUR_PALETTE.map(colour => (
                <button
                  key={colour}
                  type="button"
                  onClick={() => handlePickPreset(colour)}
                  className={cn(
                    "size-9 rounded-full border-2 transition-transform hover:scale-110 focus:outline-none",
                    colour === editingColour ? "border-foreground" : "border-transparent",
                  )}
                  style={{ backgroundColor: colour }}
                  aria-label={colour}
                />
              ))}
            </div>
          </div>
          <SheetFooter>
            <Button variant="outline" onClick={() => setEditingIndex(null)}>
              Cancel
            </Button>
            <Button onClick={handleApplyColour} disabled={!isValidEditHex}>
              Apply
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </ScreenCard>
  );
};

const ProfileSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Profile" />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <Profile />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { ProfileSuspense as Profile };
