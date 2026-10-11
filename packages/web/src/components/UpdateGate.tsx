import React, { Component, Suspense, useEffect } from "react";
import { App as CapacitorApp } from "@capacitor/app";
import { SplashScreen } from "@capacitor/splash-screen";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ArrowUpCircle } from "lucide-react";
import {
  useVersionRetrieveSuspense,
  versionRetrieve,
} from "@/api/generated/endpoints";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/Notice";
import { SafeAreaView } from "@/components/SafeAreaView";
import { APP_STORE_URL, PLAY_STORE_URL } from "@/constants";
import { isIosPlatform, isNativePlatform } from "@/utils/platform";

const UPDATE_CHECK_TIMEOUT_MS = 5000;

const withUpdateCheckTimeout = <T,>(promise: Promise<T>): Promise<T> => {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(
      () => reject(new Error("Update check timed out")),
      UPDATE_CHECK_TIMEOUT_MS
    );
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
};

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

const ReleaseSplashScreen: React.FC<UpdateGateProps> = ({ children }) => {
  useEffect(() => {
    SplashScreen.hide();
  }, []);
  return <>{children}</>;
};

const NativeUpdateGate: React.FC<UpdateGateProps> = ({ children }) => {
  const { data: version } = useVersionRetrieveSuspense({
    query: {
      queryFn: ({ signal }) => withUpdateCheckTimeout(versionRetrieve(signal)),
      retry: false,
    },
  });
  const { data: appInfo } = useSuspenseQuery({
    queryKey: ["capacitorAppInfo"],
    queryFn: () => withUpdateCheckTimeout(CapacitorApp.getInfo()),
    retry: false,
  });

  return (
    <ReleaseSplashScreen>
      {isBelowMinimum(appInfo.version, version.minimumClientVersion) ? (
        <UpdateRequired />
      ) : (
        children
      )}
    </ReleaseSplashScreen>
  );
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
    <FailOpenBoundary
      fallback={<ReleaseSplashScreen>{children}</ReleaseSplashScreen>}
    >
      <Suspense fallback={null}>
        <NativeUpdateGate>{children}</NativeUpdateGate>
      </Suspense>
    </FailOpenBoundary>
  );
};

export { UpdateGate };
