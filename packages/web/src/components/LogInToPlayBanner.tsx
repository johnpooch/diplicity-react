import { useLocation, useNavigate } from "react-router";
import { Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/Notice";
import { deepLinkStorage } from "@/deepLink";

const LogInToPlayBanner: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const storePath = () => {
    deepLinkStorage.setPendingPath(location.pathname + location.search);
  };

  return (
    <Notice
      icon={Globe}
      title="Play Diplomacy, free"
      message="Command a Great Power in 1900s Europe. Form alliances, negotiate, and outmaneuver your rivals — no dice, just pure strategy."
      actions={
        <div className="flex flex-col gap-2 w-full">
          <Button className="w-full" onClick={() => { storePath(); navigate("/register"); }}>
            Sign up to play
          </Button>
          <Button variant="outline" className="w-full" onClick={() => { storePath(); navigate("/"); }}>
            Log in
          </Button>
        </div>
      }
    />
  );
};

export { LogInToPlayBanner };
