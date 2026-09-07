import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { PlayerCard } from "@/components/PlayerCard";
import { johnDoeMustering } from "@/data/fixtures";
import { ArrowLeft } from "lucide-react";

const Member: React.FC = () => {
  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/player-card/all-states" aria-label="Back">
              <ArrowLeft />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold">Member</h1>
        </div>
        <div className="max-w-sm">
          <PlayerCard
            player={johnDoeMustering}
            presentation="identity"
            to="/player-profile/stat-grid"
          />
        </div>
      </ScreenContainer>
    </HomeShell>
  );
};

export { Member };
