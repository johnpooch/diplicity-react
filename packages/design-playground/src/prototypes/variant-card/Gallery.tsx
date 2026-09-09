import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import { VariantCard } from "@/components/VariantCard";
import {
  classicalVariant,
  sengokuVariant,
  unconstitutionalVariant,
} from "@/data/fixtures";
import type { Variant } from "@/data/types";

interface Scenario {
  label: string;
  variant: Variant;
}

const scenarios: Scenario[] = [
  { label: "Overflowing description", variant: sengokuVariant },
  { label: "Short description", variant: classicalVariant },
  { label: "Very long description", variant: unconstitutionalVariant },
];

const detailPath = (variant: Variant) =>
  `/variant-detail/full-page/${variant.id}`;

const Gallery: React.FC = () => {
  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <ScreenHeader title="Variant card" />
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              On game info
            </p>
            <div className="max-w-sm">
              <p className="mb-2 text-sm text-muted-foreground">variant</p>
              <VariantCard
                compact
                variant={sengokuVariant}
                to={detailPath(sengokuVariant)}
              />
            </div>
          </div>
          {scenarios.map(scenario => (
            <div key={scenario.label} className="flex flex-col gap-2">
              <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {scenario.label}
              </p>
              <VariantCard
                variant={scenario.variant}
                to={detailPath(scenario.variant)}
              />
            </div>
          ))}
        </div>
      </ScreenContainer>
    </HomeShell>
  );
};

export { Gallery };
