import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import { AddPlayerCard, PlayerCard } from "@/components/PlayerCard";
import {
  janeDoe,
  janeDoeActive,
  janeDoeAnon,
  janeDoeMustering,
  johnDoe,
  johnDoeActive,
  johnDoeAnon,
  johnDoeMustering,
  johnDoeNoPreferences,
  theChancellor,
  theChancellorActive,
  theChancellorMustering,
} from "@/data/fixtures";
import { Send } from "lucide-react";
import type { Player, PlayerCardPresentation } from "@/data/types";

interface Scenario {
  label: string;
  player: Player;
  presentation: PlayerCardPresentation;
}

const memberPath = "/player-card/member-destination";
const profilePath = "/player-profile/stat-grid";

const identityScenarios: Scenario[] = [
  {
    label: "Current user, no preferences",
    player: johnDoeNoPreferences,
    presentation: "identity",
  },
  {
    label: "Admin, preferred nation",
    player: johnDoe,
    presentation: "identity",
  },
  {
    label: "Assigned nation",
    player: janeDoe,
    presentation: "identity",
  },
  {
    label: "Bot, no nation",
    player: theChancellor,
    presentation: "identity",
  },
  {
    label: "Mustering, confirmed",
    player: johnDoeMustering,
    presentation: "identity",
  },
  {
    label: "Mustering, assigned and not confirmed",
    player: janeDoeMustering,
    presentation: "identity",
  },
  {
    label: "Mustering, bot confirmed",
    player: theChancellorMustering,
    presentation: "identity",
  },
];

const nationScenarios: Scenario[] = [
  {
    label: "Active, admin",
    player: johnDoeActive,
    presentation: "nation",
  },
  {
    label: "Active",
    player: janeDoeActive,
    presentation: "nation",
  },
  {
    label: "Active, bot",
    player: theChancellorActive,
    presentation: "nation",
  },
  {
    label: "Anonymous admin",
    player: johnDoeAnon,
    presentation: "nation",
  },
  {
    label: "Anonymous",
    player: janeDoeAnon,
    presentation: "nation",
  },
];

const Gallery: React.FC = () => {
  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <ScreenHeader title="Player card" />

        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              On the players list
            </p>
            <p className="text-sm text-muted-foreground">
              Press goes to the member screen.
            </p>
            <div className="flex max-w-sm flex-col gap-2">
              <PlayerCard
                player={johnDoe}
                presentation="identity"
                to={memberPath}
              />
              <PlayerCard
                player={janeDoe}
                presentation="identity"
                to={memberPath}
              />
              <PlayerCard
                player={theChancellor}
                presentation="identity"
                to={memberPath}
              />
              <AddPlayerCard
                label="Add player"
                icon={Send}
                to={memberPath}
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              On the member screen
            </p>
            <p className="text-sm text-muted-foreground">
              Press goes to the player profile.
            </p>
            <div className="max-w-sm">
              <PlayerCard
                player={johnDoeMustering}
                presentation="identity"
                to={profilePath}
              />
            </div>
          </div>

          {[...identityScenarios, ...nationScenarios].map(scenario => (
            <div key={scenario.label} className="flex flex-col gap-2">
              <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {scenario.label}
              </p>
              <div className="max-w-sm">
                <PlayerCard
                  player={scenario.player}
                  presentation={scenario.presentation}
                  to={memberPath}
                />
              </div>
            </div>
          ))}

          <div className="flex flex-col gap-2">
            <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Join, as a non-member
            </p>
            <div className="max-w-sm">
              <AddPlayerCard label="Join game" to={memberPath} />
            </div>
          </div>
        </div>
      </ScreenContainer>
    </HomeShell>
  );
};

export { Gallery };
