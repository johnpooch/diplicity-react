import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { StaticMap } from "@/components/StaticMap";
import { variants } from "@/data/fixtures";
import { ArrowLeft, Trophy } from "lucide-react";

interface VariantDetailProps {
  state: string;
}

const VariantDetail: React.FC<VariantDetailProps> = ({ state }) => {
  const variant = variants.find(item => item.id === state) ?? variants[0];

  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/variant-card/thumbnail-row" aria-label="Back">
              <ArrowLeft />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold">{variant.name}</h1>
        </div>
        <div className="overflow-hidden rounded-md border bg-muted">
          <StaticMap />
        </div>
        <p>{variant.description}</p>
        <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Trophy className="size-4 shrink-0" />
          {variant.victoryConditions}
        </p>
      </ScreenContainer>
    </HomeShell>
  );
};

export { VariantDetail };
