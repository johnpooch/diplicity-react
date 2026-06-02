import { useLocation, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { deepLinkStorage } from "@/deepLink";
import { isIosPlatform, isNativePlatform } from "@/utils/platform";

const LogInToPlayBanner: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const storePath = () => {
    deepLinkStorage.setPendingPath(location.pathname + location.search);
  };

  return (
    <div className="flex flex-col items-center gap-3 text-center">
      <div className="flex items-center gap-2">
        <DiplicityLogo />
        <p className="text-2xl font-bold">Diplicity</p>
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-xs text-muted-foreground">
          A digital implementation of Diplomacy — the legendary game of negotiation, alliance, and betrayal.
        </p>
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={() => { storePath(); navigate("/"); }}>
          Sign in
        </Button>
        <Button size="sm" variant="outline" onClick={() => { storePath(); navigate("/register"); }}>
          Register
        </Button>
      </div>
      {(!isNativePlatform() || isIosPlatform()) && (
        <a
          href="https://apps.apple.com/app/id6759169536"
          target="_blank"
          rel="noreferrer"
        >
          <img
            src="https://tools.applemediaservices.com/api/badges/download-on-the-app-store/black/en-us"
            alt="Download on the App Store"
            className="h-8"
          />
        </a>
      )}
    </div>
  );
};

export { LogInToPlayBanner };
