import React, { Component, Suspense } from "react";
import { App as CapacitorApp } from "@capacitor/app";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ArrowUpCircle } from "lucide-react";
import { useVersionRetrieveSuspense } from "@/api/generated/endpoints";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/Notice";
import { SafeAreaView } from "@/components/SafeAreaView";
import { APP_STORE_URL, PLAY_STORE_URL } from "@/constants";
import { isIosPlatform, isNativePlatform } from "@/utils/platform";

const parseVersion = (version: string): number[] =>
  version.split(".").map((part) => Number.parseInt(part, 10) || 0);

const isBelowMinimum = (current: string, minimum: string): boolean => {
  const currentParts = parseVersion(current);
  const minimumParts = parseVersion(minimum);
  const length = Math.max(currentParts.length, minimumParts.length);
  for (let i = 0; i < length; i++) {
    const currentPart = currentParts[i] ?? 0;
    const minimumPart = minimumParts[i] ?? 0;
    if (currentPart !== minimumPart) return currentPart < minimumPart;
  }
  return false;
};

const UpdateRequired: React.FC = () => (
  <div className="max-w-sm mx-auto">
    <SafeAreaView className="flex flex-col items-center justify-center min-h-screen">
      <Notice
        icon={ArrowUpCircle}
        title="Update required"
        message="This version of Diplicity is no longer supported. Update to the latest version to keep playing."
        actions={
          <Button asChild>
            <a
              href={isIosPlatform() ? APP_STORE_URL : PLAY_STORE_URL}
              target="_blank"
              rel="noreferrer"
            >
              Update Diplicity
            </a>
          </Button>
        }
      />
    </SafeAreaView>
  </div>
);

interface UpdateGateProps {
  children: React.ReactNode;
}

const NativeUpdateGate: React.FC<UpdateGateProps> = ({ children }) => {
  const { data: version } = useVersionRetrieveSuspense();
  const { data: appInfo } = useSuspenseQuery({
    queryKey: ["capacitorAppInfo"],
    queryFn: () => CapacitorApp.getInfo(),
  });

  if (isBelowMinimum(appInfo.version, version.minimumClientVersion)) {
    return <UpdateRequired />;
  }
  return <>{children}</>;
};

interface FailOpenBoundaryProps {
  children: React.ReactNode;
  fallback: React.ReactNode;
}

interface FailOpenBoundaryState {
  failed: boolean;
}

class FailOpenBoundary extends Component<
  FailOpenBoundaryProps,
  FailOpenBoundaryState
> {
  constructor(props: FailOpenBoundaryProps) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError(): FailOpenBoundaryState {
    return { failed: true };
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

const UpdateGate: React.FC<UpdateGateProps> = ({ children }) => {
  if (!isNativePlatform()) return <>{children}</>;
  return (
    <FailOpenBoundary fallback={children}>
      <Suspense fallback={null}>
        <NativeUpdateGate>{children}</NativeUpdateGate>
      </Suspense>
    </FailOpenBoundary>
  );
};

export { UpdateGate };
