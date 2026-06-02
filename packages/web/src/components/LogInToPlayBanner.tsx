import { useLocation, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  EmptyDescription,
  EmptyContent,
} from "@/components/ui/empty";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { deepLinkStorage } from "@/deepLink";

const LogInToPlayBanner: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const storePath = () => {
    deepLinkStorage.setPendingPath(location.pathname + location.search);
  };

  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="image">
          <DiplicityLogo />
        </EmptyMedia>
        <EmptyTitle>Register to play</EmptyTitle>
        <EmptyDescription>
          Diplomacy is the legendary game of negotiation, alliance, and betrayal — a war where every move is decided by the people playing, not by chance.
        </EmptyDescription>
      </EmptyHeader>
      <EmptyContent>
        <div className="flex flex-col gap-2 w-full">
          <Button className="w-full" onClick={() => { storePath(); navigate("/register"); }}>
            Sign up to play
          </Button>
          <Button variant="outline" className="w-full" onClick={() => { storePath(); navigate("/"); }}>
            Log in
          </Button>
        </div>
      </EmptyContent>
    </Empty>
  );
};

export { LogInToPlayBanner };
