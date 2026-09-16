import React from "react";
import { useNavigate } from "react-router";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { useMessaging } from "@/hooks/useMessaging";
import { useTheme } from "@/theme/useTheme";
import type { ThemePreference } from "@/theme/themeStorage";

const themeOptions: { value: ThemePreference; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
];

export const AccountSettingsCard: React.FC = () => {
  const navigate = useNavigate();
  const { preference, setPreference } = useTheme();
  const {
    enableMessaging,
    enabled,
    disableMessaging,
    permissionDenied,
    error,
  } = useMessaging();

  const notificationsOn = !permissionDenied && enabled;

  const handleTogglePushNotifications = (checked: boolean) => {
    if (checked) {
      enableMessaging();
    } else {
      disableMessaging();
    }
  };

  return (
    <Card>
      <CardContent className="flex flex-col gap-4">
        <div className="space-y-3">
          <h2 className="font-semibold">Appearance</h2>
          <RadioGroup
            value={preference}
            onValueChange={setPreference}
            className="flex flex-row gap-4"
          >
            {themeOptions.map(option => (
              <div key={option.value} className="flex items-center gap-2">
                <RadioGroupItem
                  value={option.value}
                  id={`theme-${option.value}`}
                />
                <Label htmlFor={`theme-${option.value}`}>{option.label}</Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        <Separator />

        <div className="flex flex-col gap-4 sm:flex-row sm:gap-6">
          <div className="space-y-2 sm:flex-1">
            <h2 className="font-semibold">Notifications</h2>
            <div className="flex items-center gap-2">
              <Switch
                id="push-notifications"
                checked={notificationsOn}
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
            {!notificationsOn && (
              <p className="text-sm text-destructive">
                You won&apos;t be informed if someone messages you or a game
                proceeds.
              </p>
            )}
          </div>

          <Separator
            orientation="vertical"
            className="hidden self-stretch data-[orientation=vertical]:h-auto sm:block"
          />

          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-destructive">
              Danger Zone
            </h2>
            <Button
              variant="outline"
              className="text-destructive border-destructive hover:bg-destructive/10 hover:text-destructive dark:hover:bg-destructive/10"
              onClick={() => navigate("/delete-account")}
            >
              Delete Account
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
