import React from "react";
import { WifiOff } from "lucide-react";
import { DiplicityLogo } from "./DiplicityLogo";
import { PrimaryButton, SecondaryButton } from "@/components/ui/role-buttons";
import { SafeAreaView } from "@/components/SafeAreaView";
import { Notice } from "@/components/Notice";
import { useNetworkStatus } from "@/hooks";

interface OfflineNoticeProps {
  onRetry: () => void;
  fullScreen?: boolean;
}

const OfflineNotice: React.FC<OfflineNoticeProps> = ({ onRetry, fullScreen }) => {
  const online = useNetworkStatus();
  const wasOffline = React.useRef(!online);

  React.useEffect(() => {
    if (online && wasOffline.current) {
      onRetry();
    }
    wasOffline.current = !online;
  }, [online, onRetry]);

  if (fullScreen) {
    return (
      <div className="max-w-sm mx-auto">
        <SafeAreaView className="flex flex-col items-center justify-center min-h-screen text-center gap-6">
          <DiplicityLogo />
          <h1 className="text-2xl font-bold">No internet connection</h1>
          <p className="text-muted-foreground">
            Diplicity needs a connection to load. Check your connection and try
            again.
          </p>
          <SecondaryButton onClick={onRetry}>
            Try Again
          </SecondaryButton>
        </SafeAreaView>
      </div>
    );
  }

  return (
    <Notice
      icon={WifiOff}
      title="No internet connection"
      message="Check your connection and try again."
      actions={<PrimaryButton onClick={onRetry}>Try Again</PrimaryButton>}
    />
  );
};

export { OfflineNotice };
