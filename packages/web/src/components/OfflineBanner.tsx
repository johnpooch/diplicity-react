import React from "react";
import { WifiOff } from "lucide-react";
import { useNetworkStatus } from "@/hooks";

const OfflineBanner: React.FC = () => {
  const online = useNetworkStatus();

  if (online) return null;

  return (
    <div className="flex items-center justify-center gap-2 border-b bg-muted px-4 py-2 text-sm text-muted-foreground">
      <WifiOff className="size-4" />
      No internet connection
    </div>
  );
};

export { OfflineBanner };
