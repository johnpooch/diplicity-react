import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useVariant } from "@/hooks/useVariant";
import { downloadSchemaJson } from "@/utils/schemaExport";
import { Download, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import type { VariantDefinition } from "@/types/variant";

interface Warning {
  message: string;
}

function collectWarnings(variant: VariantDefinition): Warning[] {
  const warnings: Warning[] = [];

  const isolated = variant.provinces.filter((p) => p.adjacencies.length === 0);
  if (isolated.length > 0) {
    const names = isolated.map((p) => p.name || p.id).join(", ");
    warnings.push({ message: `${isolated.length} province(s) have no adjacencies: ${names}` });
  }

  const missingId = variant.provinces.filter((p) => !p.id.trim());
  if (missingId.length > 0) {
    warnings.push({ message: `${missingId.length} province(s) have no ID set` });
  }

  const supplyWithoutHome = variant.provinces.filter(
    (p) => p.supplyCenter && !p.homeNation
  );
  if (supplyWithoutHome.length > 0) {
    warnings.push({
      message: `${supplyWithoutHome.length} supply center(s) have no home nation — they will start neutral`,
    });
  }

  return warnings;
}

export function PhaseExport() {
  const { variant } = useVariant();

  if (!variant) return null;

  const warnings = collectWarnings(variant);

  const landCount = variant.provinces.filter((p) => p.type === "land" || p.type === "namedCoasts").length;
  const seaCount = variant.provinces.filter((p) => p.type === "sea").length;
  const coastalCount = variant.provinces.filter((p) => p.type === "coastal").length;
  const supplyCenterCount = variant.provinces.filter((p) => p.supplyCenter).length;
  const unitCount = variant.provinces.filter((p) => p.startingUnit !== null).length;

  const handleDownload = () => {
    downloadSchemaJson(variant);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{variant.name || "Unnamed Variant"}</h2>
        {variant.description && (
          <p className="mt-1 text-muted-foreground">{variant.description}</p>
        )}
        {variant.author && (
          <p className="text-sm text-muted-foreground">by {variant.author}</p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Nations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{variant.nations.length}</p>
            <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
              {variant.nations.map((n) => (
                <li key={n.id} className="flex items-center gap-2">
                  <span
                    className="inline-block h-3 w-3 rounded-full"
                    style={{ backgroundColor: n.color }}
                  />
                  {n.name}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Provinces</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{variant.provinces.length}</p>
            <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
              <li>Land: {landCount}</li>
              <li>Sea: {seaCount}</li>
              <li>Coastal: {coastalCount}</li>
              {variant.namedCoasts.length > 0 && (
                <li>Named coasts: {variant.namedCoasts.length}</li>
              )}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Supply Centers</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{supplyCenterCount}</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Solo victory at {variant.soloVictorySCCount} SCs
            </p>
            <p className="text-sm text-muted-foreground">
              Starting year: {variant.startYear}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Starting Units</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{unitCount}</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Placed in home provinces
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Info className="h-4 w-4 text-muted-foreground" />
            Assumed defaults
          </CardTitle>
          <CardDescription>
            These fields are not configured in the wizard and will use standard values.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>
              <span className="font-medium text-foreground">Phase progression:</span>{" "}
              Classical (Spring/Fall cycle with Retreat and Adjustment phases)
            </li>
            <li>
              <span className="font-medium text-foreground">Adjacency pass type:</span>{" "}
              Inferred from province types (sea→fleet, coastal↔coastal→both, otherwise army)
            </li>
          </ul>
        </CardContent>
      </Card>

      {warnings.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base text-yellow-800 dark:text-yellow-200">
              <AlertTriangle className="h-4 w-4" />
              Warnings ({warnings.length})
            </CardTitle>
            <CardDescription className="text-yellow-700 dark:text-yellow-300">
              These issues won&apos;t block export but may affect gameplay.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm text-yellow-800 dark:text-yellow-200">
              {warnings.map((w, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-0.5 shrink-0">•</span>
                  {w.message}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {warnings.length === 0 && (
        <Card className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
          <CardContent className="flex items-center gap-3 pt-6">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600 dark:text-green-400" />
            <p className="text-sm text-green-800 dark:text-green-200">
              No issues found. Your variant looks ready to export.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end">
        <Button size="lg" onClick={handleDownload} className="gap-2">
          <Download className="h-4 w-4" />
          Download JSON
        </Button>
      </div>
    </div>
  );
}
